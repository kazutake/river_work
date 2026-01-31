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
    # 「約XX億XX百万円」「XX億円」「XX,XXX千円」「XX百万円」等のパターン
    patterns = [
        # 億＋万円: 3億5000万円 → 350000000
        (r"(\d[\d,.]*)億(\d[\d,.]*)万\s*円", lambda m: int(
            float(m.group(1).replace(",", "")) * 1_0000_0000
            + float(m.group(2).replace(",", "")) * 1_0000
        )),
        # 億円: 3億円 → 300000000
        (r"(\d[\d,.]*)億\s*円", lambda m: int(
            float(m.group(1).replace(",", "")) * 1_0000_0000
        )),
        # 百万円: 350百万円 → 350000000
        (r"(\d[\d,.]*)百万\s*円", lambda m: int(
            float(m.group(1).replace(",", "")) * 100_0000
        )),
        # 千円: 350,000千円 → 350000000
        (r"(\d[\d,.]*)千\s*円", lambda m: int(
            float(m.group(1).replace(",", "")) * 1000
        )),
        # 万円: 35000万円 → 350000000
        (r"(\d[\d,.]*)万\s*円", lambda m: int(
            float(m.group(1).replace(",", "")) * 1_0000
        )),
        # 普通の円: 350,000,000円
        (r"(\d{1,3}(?:,\d{3})+)\s*円", lambda m: int(
            m.group(1).replace(",", "")
        )),
        # 数字+円（7桁以上のみ: 少額を除外）
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
    if any(kw in text for kw in ["業務委託", "業務", "検討", "策定", "調査", "解析", "設計業務"]):
        return "業務委託"
    if any(kw in text for kw in ["工事", "施工", "築造", "改修工事"]):
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

        return articles

    async def _collect_main_page(self) -> list[dict]:
        """メインの入札・契約ページから情報を収集"""
        articles = []
        soup = await self.fetch_page(self.base_url)
        if not soup:
            return articles

        seen_urls = set()

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
                articles.append(self._build_article(
                    text, full_url, self.base_url, date, "発注情報",
                ))

            # 入札関連ページへのリンク（河川フィルタなし）も収集
            elif self._is_procurement_link(text):
                seen_urls.add(full_url)
                date = self._extract_date_from_context(link)
                articles.append(self._build_article(
                    text, full_url, self.base_url, date, "入札公告",
                ))

        return articles

    async def _collect_bid_notices(self) -> list[dict]:
        """入札公告ページを探索して収集"""
        articles = []
        soup = await self.fetch_page(self.base_url)
        if not soup:
            return articles

        # 入札公告へのリンクを探す
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
            # URLパスから推測
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

            seen_urls = set()
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

                # 河川関連の発注をフィルタ
                if self._is_river_procurement(text):
                    seen_urls.add(full_url)
                    date = self._extract_date_from_context(link)
                    articles.append(self._build_article(
                        text, full_url, url, date, "入札公告",
                    ))

        return articles

    async def _collect_planned_orders(self) -> list[dict]:
        """発注見通し・発注予定の収集"""
        articles = []
        soup = await self.fetch_page(self.base_url)
        if not soup:
            return articles

        # 発注見通し・予定ページを探す
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

            # PDF リンクも含めて取得（発注見通しはPDFが多い）
            seen_urls = set()
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
                    articles.append(self._build_article(
                        text, full_url, url, date, "発注見通し",
                    ))

        return articles

    # --------------------------------------------------
    # 記事生成ヘルパー
    # --------------------------------------------------

    def _build_article(self, text: str, full_url: str, source_url: str,
                       date: str | None, category: str) -> dict:
        """記事dictを生成し、金額・業務分類情報も付与する"""
        return {
            "source": self.source_name,
            "source_url": source_url,
            "title": text[:200],
            "url": full_url,
            "published_date": date,
            "collected_date": datetime.now().strftime("%Y-%m-%d"),
            "category": category,
            "region": self.region,
            # 発注詳細（collector_manager が DB に保存）
            "estimated_amount": extract_amount(text),
            "business_type": classify_business_type(text),
            "procurement_method": classify_procurement_method(text),
            "kadou_category": classify_kadou_category(text),
        }

    # --------------------------------------------------
    # 判定メソッド
    # --------------------------------------------------

    def _is_river_procurement(self, text: str) -> bool:
        """河川関連の発注情報か判定"""
        # 河川系キーワード
        river_kw = [
            "河川", "治水", "堤防", "護岸", "ダム", "砂防",
            "水門", "樋門", "排水機場", "床止め", "水制",
            "河道", "浚渫", "掘削", "築堤", "引堤",
            "洪水", "浸水", "氾濫", "水害", "水防",
            "流域", "水管理", "水質",
        ]
        # 技術系キーワード
        tech_kw = [
            "シミュレーション", "解析", "数値計算", "予測",
            "測量", "設計", "調査", "検討",
        ]
        # 発注系キーワード
        proc_kw = [
            "入札", "公告", "発注", "業務委託",
            "プロポーザル", "総合評価", "工事",
        ]

        has_river = any(kw in text for kw in river_kw)
        has_tech = any(kw in text for kw in tech_kw)
        has_proc = any(kw in text for kw in proc_kw)

        # 河川 + 発注、河川 + 技術、いずれかでマッチ
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
        # 同じ mlit.go.jp 系列を許容
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

        # dt-dd 構造
        if parent and parent.name == "dd":
            dt = parent.find_previous_sibling("dt")
            if dt:
                date = self.extract_date_from_text(dt.get_text())
                if date:
                    return date

        # テーブル行
        if parent and parent.name in ("td", "th"):
            row = parent.find_parent("tr")
            if row:
                date = self.extract_date_from_text(row.get_text())
                if date:
                    return date

        return None
