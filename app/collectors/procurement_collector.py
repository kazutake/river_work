"""公共事業 発注情報コレクター"""

import logging
import re
from datetime import datetime
from urllib.parse import urlparse

from .base_collector import BaseCollector
from ..config import KADOU_BUSINESS_CATEGORIES

logger = logging.getLogger(__name__)


def extract_amount(text: str) -> int | None:
    """テキストから金額（円）を抽出する。複数ある場合は最大値を返す。"""
    amounts = []
    patterns = [
        # 億＋万円: 3億5000万円
        (r"(\d[\d,.]*)億(\d[\d,.]*)万\s*円", lambda m: int(
            float(m.group(1).replace(",", "")) * 1_0000_0000
            + float(m.group(2).replace(",", "")) * 1_0000
        )),
        # 億円: 3億円
        (r"(\d[\d,.]*)億\s*円", lambda m: int(
            float(m.group(1).replace(",", "")) * 1_0000_0000
        )),
        # 百万円: 350百万円
        (r"(\d[\d,.]*)百万\s*円", lambda m: int(
            float(m.group(1).replace(",", "")) * 100_0000
        )),
        # 千円: 350,000千円
        (r"(\d[\d,.]*)千\s*円", lambda m: int(
            float(m.group(1).replace(",", "")) * 1000
        )),
        # 万円: 35000万円
        (r"(\d[\d,.]*)万\s*円", lambda m: int(
            float(m.group(1).replace(",", "")) * 1_0000
        )),
        # 普通の円: 350,000,000円
        (r"(\d{1,3}(?:,\d{3})+)\s*円", lambda m: int(
            m.group(1).replace(",", "")
        )),
        # 数字+円（7桁以上のみ）
        (r"(\d{7,})\s*円", lambda m: int(m.group(1))),
    ]

    for pattern, parser in patterns:
        for match in re.finditer(pattern, text):
            try:
                val = parser(match)
                if val and val >= 100_0000:  # 100万円以上のみ
                    amounts.append(val)
            except (ValueError, IndexError):
                continue

    return max(amounts) if amounts else None


def classify_kadou_category(text: str) -> str | None:
    """テキストから河道計画・設計の業務カテゴリを判定"""
    for category, keywords in KADOU_BUSINESS_CATEGORIES.items():
        if any(kw in text for kw in keywords):
            return category
    return None


def classify_business_type(text: str) -> str | None:
    """業務種別を判定（業務委託 / 工事）"""
    if any(kw in text for kw in ["業務委託", "設計業務", "調査業務", "解析業務",
                                   "検討業務", "測量業務", "策定業務", "計画業務"]):
        return "業務委託"
    if any(kw in text for kw in ["業務", "検討", "策定", "調査", "解析",
                                   "設計", "計画", "測量"]):
        return "業務委託"
    if any(kw in text for kw in ["工事", "施工", "築造", "改修工事", "整備工事"]):
        return "工事"
    return None


def classify_procurement_method(text: str) -> str | None:
    """入札方式を判定"""
    if "プロポーザル" in text or "公募型" in text:
        return "プロポーザル"
    if "総合評価" in text:
        return "総合評価落札方式"
    if "一般競争" in text:
        return "一般競争入札"
    if "指名競争" in text:
        return "指名競争入札"
    if "随意契約" in text:
        return "随意契約"
    return None


class ProcurementCollector(BaseCollector):
    """地方整備局・国交省の入札・発注情報から河川事業関連を収集する"""

    def __init__(self, name: str, url: str, region: str, bureau: str,
                 source_type: str = "bureau"):
        super().__init__(
            source_name=name,
            base_url=url,
            region=region,
        )
        self.bureau = bureau
        self.source_type = source_type

    async def collect(self) -> list[dict]:
        articles = []

        # メインページの発注情報を収集
        articles.extend(await self._collect_main_page())

        # 入札公告サブページを探索
        articles.extend(await self._collect_bid_notices())

        # 業務・工事の発注予定情報を探索
        articles.extend(await self._collect_planned_orders())

        # 落札結果・契約結果ページを探索
        articles.extend(await self._collect_bid_results())

        return articles

    async def _collect_main_page(self) -> list[dict]:
        """メインの入札・契約ページから情報を収集"""
        articles = []
        soup = await self.fetch_page(self.base_url)
        if not soup:
            return articles

        # まずテーブルから構造化データを抽出
        articles.extend(self._parse_procurement_tables(soup, self.base_url, "発注情報"))

        seen_urls = {a["url"] for a in articles}

        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            href = link["href"]
            if not text or len(text) < 4:
                continue

            full_url = self.resolve_url(href)
            if full_url in seen_urls:
                continue

            if self._is_navigation_link(text, href):
                continue

            # 河川関連の発注情報を抽出
            if self._is_river_procurement(text):
                seen_urls.add(full_url)
                date = self._extract_date_from_context(link)
                context = self._get_row_context(link)
                articles.append(self._build_article(
                    text, full_url, self.base_url, date, "発注情報", context,
                ))

            # 入札関連ページへのリンクも収集
            elif self._is_procurement_link(text):
                seen_urls.add(full_url)
                date = self._extract_date_from_context(link)
                context = self._get_row_context(link)
                articles.append(self._build_article(
                    text, full_url, self.base_url, date, "入札公告", context,
                ))

        return articles

    async def _collect_bid_notices(self) -> list[dict]:
        """入札公告ページを探索して収集"""
        articles = []
        soup = await self.fetch_page(self.base_url)
        if not soup:
            return articles

        bid_urls = set()
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            href = link["href"]
            if any(kw in text for kw in [
                "入札公告", "一般競争", "公告一覧", "公募",
                "発注見通し", "発注予定",
            ]):
                url = self.resolve_url(href)
                if self._is_safe_url(url):
                    bid_urls.add(url)
            if any(p in href.lower() for p in [
                "koukoku", "nyuusatu", "koubo", "hacchuu",
            ]):
                url = self.resolve_url(href)
                if self._is_safe_url(url):
                    bid_urls.add(url)

        for url in list(bid_urls)[:3]:
            sub_soup = await self.fetch_page(url)
            if not sub_soup:
                continue

            # テーブルから構造化データを抽出
            articles.extend(
                self._parse_procurement_tables(sub_soup, url, "入札公告")
            )

            seen_urls = {a["url"] for a in articles}
            for link in sub_soup.find_all("a", href=True):
                text = link.get_text(strip=True)
                href = link["href"]
                if not text or len(text) < 4:
                    continue

                full_url = self.resolve_url(href)
                if full_url in seen_urls:
                    continue
                if self._is_navigation_link(text, href):
                    continue

                if self._is_river_procurement(text):
                    seen_urls.add(full_url)
                    date = self._extract_date_from_context(link)
                    context = self._get_row_context(link)
                    articles.append(self._build_article(
                        text, full_url, url, date, "入札公告", context,
                    ))

        return articles

    async def _collect_planned_orders(self) -> list[dict]:
        """発注見通し・発注予定の収集"""
        articles = []
        soup = await self.fetch_page(self.base_url)
        if not soup:
            return articles

        plan_urls = set()
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            href = link["href"]
            if any(kw in text for kw in [
                "発注見通し", "発注予定", "発注計画",
                "業務発注", "工事発注",
            ]):
                url = self.resolve_url(href)
                if self._is_safe_url(url):
                    plan_urls.add(url)

        for url in list(plan_urls)[:2]:
            sub_soup = await self.fetch_page(url)
            if not sub_soup:
                continue

            articles.extend(
                self._parse_procurement_tables(sub_soup, url, "発注見通し")
            )

            seen_urls = {a["url"] for a in articles}
            for link in sub_soup.find_all("a", href=True):
                text = link.get_text(strip=True)
                href = link["href"]
                if not text or len(text) < 3:
                    continue

                full_url = self.resolve_url(href)
                if full_url in seen_urls:
                    continue

                is_pdf = href.lower().endswith(".pdf")
                if self._is_river_procurement(text) or (
                    is_pdf and any(kw in text for kw in [
                        "河川", "発注", "見通し", "予定",
                    ])
                ):
                    seen_urls.add(full_url)
                    date = self._extract_date_from_context(link)
                    context = self._get_row_context(link)
                    articles.append(self._build_article(
                        text, full_url, url, date, "発注見通し", context,
                    ))

        return articles

    async def _collect_bid_results(self) -> list[dict]:
        """落札結果・契約結果ページを探索して収集"""
        articles = []
        soup = await self.fetch_page(self.base_url)
        if not soup:
            return articles

        # 落札結果・契約結果ページへのリンクを探す
        result_urls = set()
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            href = link["href"]
            if any(kw in text for kw in [
                "落札結果", "契約結果", "入札結果", "落札情報",
                "契約情報", "落札者", "結果公表", "契約実績",
            ]):
                url = self.resolve_url(href)
                if self._is_safe_url(url):
                    result_urls.add(url)
            if any(p in href.lower() for p in [
                "rakusatsu", "keiyaku_kekka", "kekka", "result",
            ]):
                url = self.resolve_url(href)
                if self._is_safe_url(url):
                    result_urls.add(url)

        for url in list(result_urls)[:3]:
            sub_soup = await self.fetch_page(url)
            if not sub_soup:
                continue

            # テーブルから落札結果データを抽出
            articles.extend(
                self._parse_result_tables(sub_soup, url)
            )

            # リンクからも収集
            seen_urls = {a["url"] for a in articles}
            for link in sub_soup.find_all("a", href=True):
                text = link.get_text(strip=True)
                href = link["href"]
                if not text or len(text) < 4:
                    continue
                full_url = self.resolve_url(href)
                if full_url in seen_urls:
                    continue
                if self._is_navigation_link(text, href):
                    continue
                if self._is_river_procurement(text):
                    seen_urls.add(full_url)
                    date = self._extract_date_from_context(link)
                    context = self._get_row_context(link)
                    article = self._build_article(
                        text, full_url, url, date, "落札結果", context,
                    )
                    # テーブル行から金額を抽出
                    row_amount = self._extract_amount_from_row(link)
                    if row_amount:
                        article["contract_amount"] = row_amount
                        if not article.get("estimated_amount"):
                            article["estimated_amount"] = row_amount
                    articles.append(article)

        return articles

    # --------------------------------------------------
    # テーブル解析
    # --------------------------------------------------

    def _parse_procurement_tables(self, soup, source_url: str,
                                  category: str) -> list[dict]:
        """発注情報テーブルからデータを構造化抽出"""
        articles = []

        for table in soup.find_all("table"):
            headers = self._get_table_headers(table)
            if not headers:
                continue

            name_col = self._find_column_index(headers, [
                "業務名", "工事名", "件名", "案件名", "名称",
                "業務・工事名", "業務概要", "工事概要",
            ])
            if name_col is None:
                continue

            amount_col = self._find_column_index(headers, [
                "予定価格", "設計金額", "予算額", "概算額", "金額",
            ])
            method_col = self._find_column_index(headers, [
                "入札方式", "方式", "契約方式", "発注方式",
            ])
            type_col = self._find_column_index(headers, [
                "種別", "業務種別", "分類",
            ])

            for row in table.find_all("tr")[1:]:
                cells = row.find_all(["td", "th"])
                if len(cells) <= name_col:
                    continue

                name = cells[name_col].get_text(strip=True)
                if not name or len(name) < 3:
                    continue
                if not self._is_river_procurement(name):
                    continue

                row_text = " ".join(c.get_text(strip=True) for c in cells)

                estimated_amt = None
                if amount_col is not None and len(cells) > amount_col:
                    estimated_amt = extract_amount(
                        cells[amount_col].get_text(strip=True)
                    )
                if not estimated_amt:
                    estimated_amt = extract_amount(row_text)

                method = None
                if method_col is not None and len(cells) > method_col:
                    method = classify_procurement_method(
                        cells[method_col].get_text(strip=True)
                    )
                if not method:
                    method = classify_procurement_method(row_text)

                biz_type = None
                if type_col is not None and len(cells) > type_col:
                    biz_type = classify_business_type(
                        cells[type_col].get_text(strip=True)
                    )
                if not biz_type:
                    biz_type = classify_business_type(name)

                link = cells[name_col].find("a", href=True)
                if link:
                    full_url = self.resolve_url(link["href"])
                else:
                    full_url = source_url + "#row-" + str(abs(hash(name)))[:10]

                date = self.extract_date_from_text(row_text)

                articles.append({
                    "source": self.source_name,
                    "source_url": source_url,
                    "title": name[:200],
                    "content": row_text[:500],
                    "url": full_url,
                    "published_date": date,
                    "collected_date": datetime.now().strftime("%Y-%m-%d"),
                    "category": category,
                    "region": self.region,
                    "estimated_amount": estimated_amt,
                    "business_type": biz_type,
                    "procurement_method": method,
                    "kadou_category": classify_kadou_category(
                        name + " " + row_text
                    ),
                })

        return articles

    def _parse_result_tables(self, soup, source_url: str) -> list[dict]:
        """落札結果テーブルからデータを抽出"""
        articles = []

        for table in soup.find_all("table"):
            headers = self._get_table_headers(table)
            if not headers:
                continue

            name_col = self._find_column_index(headers, [
                "業務名", "工事名", "件名", "案件名", "名称",
                "業務・工事名",
            ])
            if name_col is None:
                continue

            contract_col = self._find_column_index(headers, [
                "落札金額", "契約金額", "落札額", "契約額",
                "落札価格", "契約価格",
            ])
            est_col = self._find_column_index(headers, [
                "予定価格", "設計金額", "予算額",
            ])
            method_col = self._find_column_index(headers, [
                "入札方式", "方式", "契約方式",
            ])
            winner_col = self._find_column_index(headers, [
                "落札者", "契約者", "受注者", "落札業者",
            ])

            for row in table.find_all("tr")[1:]:
                cells = row.find_all(["td", "th"])
                if len(cells) <= name_col:
                    continue

                name = cells[name_col].get_text(strip=True)
                if not name or len(name) < 3:
                    continue
                if not self._is_river_procurement(name):
                    continue

                row_text = " ".join(c.get_text(strip=True) for c in cells)

                contract_amt = None
                estimated_amt = None
                if contract_col is not None and len(cells) > contract_col:
                    contract_amt = extract_amount(
                        cells[contract_col].get_text(strip=True)
                    )
                if est_col is not None and len(cells) > est_col:
                    estimated_amt = extract_amount(
                        cells[est_col].get_text(strip=True)
                    )
                if not contract_amt and not estimated_amt:
                    row_amount = extract_amount(row_text)
                    if row_amount:
                        contract_amt = row_amount

                method = None
                if method_col is not None and len(cells) > method_col:
                    method = classify_procurement_method(
                        cells[method_col].get_text(strip=True)
                    )

                winner = ""
                if winner_col is not None and len(cells) > winner_col:
                    winner = cells[winner_col].get_text(strip=True)

                link = cells[name_col].find("a", href=True)
                if link:
                    full_url = self.resolve_url(link["href"])
                else:
                    full_url = source_url + "#result-" + str(abs(hash(name)))[:10]

                date = self.extract_date_from_text(row_text)

                content_parts = [row_text]
                if winner:
                    content_parts.append(f"落札者: {winner}")

                articles.append({
                    "source": self.source_name,
                    "source_url": source_url,
                    "title": name[:200],
                    "content": " ".join(content_parts)[:500],
                    "url": full_url,
                    "published_date": date,
                    "collected_date": datetime.now().strftime("%Y-%m-%d"),
                    "category": "落札結果",
                    "region": self.region,
                    "estimated_amount": estimated_amt or contract_amt,
                    "contract_amount": contract_amt,
                    "business_type": classify_business_type(name),
                    "procurement_method": (
                        method or classify_procurement_method(name)
                    ),
                    "kadou_category": classify_kadou_category(
                        name + " " + row_text
                    ),
                })

        return articles

    def _get_table_headers(self, table) -> list[str]:
        """テーブルのヘッダー行を取得"""
        thead = table.find("thead")
        if thead:
            header_row = thead.find("tr")
            if header_row:
                return [th.get_text(strip=True)
                        for th in header_row.find_all(["th", "td"])]

        first_row = table.find("tr")
        if first_row:
            ths = first_row.find_all("th")
            if ths:
                return [th.get_text(strip=True) for th in ths]

        return []

    def _find_column_index(self, headers: list[str],
                           keywords: list[str]) -> int | None:
        """ヘッダーからキーワードに一致する列インデックスを返す"""
        for i, header in enumerate(headers):
            for kw in keywords:
                if kw in header:
                    return i
        return None

    # --------------------------------------------------
    # 記事生成ヘルパー
    # --------------------------------------------------

    def _build_article(self, text: str, full_url: str, source_url: str,
                       date: str | None, category: str,
                       context_text: str = "") -> dict:
        """記事dictを生成し、金額・業務分類情報も付与する"""
        full_text = text + " " + context_text
        return {
            "source": self.source_name,
            "source_url": source_url,
            "title": text[:200],
            "content": context_text[:500] if context_text else None,
            "url": full_url,
            "published_date": date,
            "collected_date": datetime.now().strftime("%Y-%m-%d"),
            "category": category,
            "region": self.region,
            "estimated_amount": extract_amount(full_text),
            "business_type": classify_business_type(full_text),
            "procurement_method": classify_procurement_method(full_text),
            "kadou_category": classify_kadou_category(full_text),
        }

    # --------------------------------------------------
    # コンテキスト抽出ヘルパー
    # --------------------------------------------------

    def _get_row_context(self, element) -> str:
        """リンク要素の周辺コンテキスト（テーブル行等）のテキストを返す"""
        parent = element.parent
        while parent:
            if parent.name == "tr":
                return parent.get_text(separator=" ", strip=True)
            if parent.name in ("li", "dd", "dt"):
                return parent.get_text(separator=" ", strip=True)
            if parent.name in ("div", "section", "body", "table"):
                break
            parent = parent.parent

        if element.parent:
            return element.parent.get_text(separator=" ", strip=True)[:300]
        return ""

    def _extract_amount_from_row(self, element) -> int | None:
        """リンク要素のテーブル行から金額を抽出"""
        parent = element.parent
        while parent:
            if parent.name == "tr":
                text = parent.get_text()
                return extract_amount(text)
            if parent.name in ("body", "table"):
                break
            parent = parent.parent
        return None

    # --------------------------------------------------
    # 判定メソッド
    # --------------------------------------------------

    def _is_river_procurement(self, text: str) -> bool:
        """河川関連の発注情報か判定"""
        river_kw = [
            "河川", "治水", "堤防", "護岸", "ダム", "砂防",
            "水門", "樋門", "排水機場", "床止め", "水制",
            "河道", "浚渫", "掘削", "築堤", "引堤",
            "洪水", "浸水", "氾濫", "水害", "水防",
            "流域", "水管理", "水質",
        ]
        tech_kw = [
            "シミュレーション", "解析", "数値計算", "予測",
            "測量", "設計", "調査", "検討",
        ]
        proc_kw = [
            "入札", "公告", "発注", "業務委託", "業務",
            "プロポーザル", "総合評価", "工事", "委託",
        ]

        has_river = any(kw in text for kw in river_kw)
        has_tech = any(kw in text for kw in tech_kw)
        has_proc = any(kw in text for kw in proc_kw)

        return has_river or (has_tech and has_proc)

    def _is_procurement_link(self, text: str) -> bool:
        """一般的な発注・入札リンクか判定"""
        keywords = [
            "一般競争入札", "入札公告", "公募", "発注見通し",
            "発注予定", "契約結果", "落札結果", "業務発注",
        ]
        return any(kw in text for kw in keywords)

    def _is_navigation_link(self, text: str, href: str) -> bool:
        """ナビゲーションリンクを除外"""
        nav_texts = [
            "トップ", "ホーム", "サイトマップ", "アクセス",
            "リンク集", "問い合わせ", "English", "ページの先頭",
            "戻る", "一覧へ", "プライバシー", "著作権", "免責",
        ]
        if any(t in text for t in nav_texts):
            return True
        if href.startswith(("javascript:", "mailto:", "#", "tel:")):
            return True
        return False

    def _is_safe_url(self, url: str) -> bool:
        """同一ドメインまたは同一整備局ドメインか判定"""
        base_host = urlparse(self.base_url).netloc
        target_host = urlparse(url).netloc
        if base_host == target_host:
            return True
        if "mlit.go.jp" in base_host and "mlit.go.jp" in target_host:
            return True
        return False

    def _extract_date_from_context(self, element) -> str | None:
        """要素周辺から日付を抽出"""
        parent = element.parent
        if parent:
            text = parent.get_text()
            date = self.extract_date_from_text(text)
            if date:
                return date

        for sibling in [element.previous_sibling, element.next_sibling]:
            if sibling and hasattr(sibling, "get_text"):
                date = self.extract_date_from_text(sibling.get_text())
                if date:
                    return date
            elif isinstance(sibling, str):
                date = self.extract_date_from_text(sibling)
                if date:
                    return date

        if parent and parent.name == "dd":
            dt = parent.find_previous_sibling("dt")
            if dt:
                date = self.extract_date_from_text(dt.get_text())
                if date:
                    return date

        if parent and parent.name in ("td", "th"):
            row = parent.find_parent("tr")
            if row:
                date = self.extract_date_from_text(row.get_text())
                if date:
                    return date

        return None
