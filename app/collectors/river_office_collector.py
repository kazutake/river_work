"""全国河川事務所 情報コレクター"""

import logging
import re
from datetime import datetime
from urllib.parse import urlparse

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class RiverOfficeCollector(BaseCollector):
    """各河川事務所のHPからお知らせ・事業情報・記者発表等を収集する"""

    def __init__(self, name: str, url: str, region: str, bureau: str):
        super().__init__(
            source_name=name,
            base_url=url,
            region=region,
        )
        self.bureau = bureau

    async def collect(self) -> list[dict]:
        articles = []

        # トップページの新着情報・お知らせを収集
        articles.extend(await self._collect_top_page())

        # 記者発表ページを探索
        articles.extend(await self._collect_press_page())

        # 入札・契約情報ページを探索
        articles.extend(await self._collect_office_procurement())

        return articles

    async def _collect_top_page(self) -> list[dict]:
        """トップページの新着・お知らせ一覧を収集"""
        articles = []
        soup = await self.fetch_page(self.base_url)
        if not soup:
            return articles

        # 新着情報・トピックス・お知らせ等のセクションを探す
        news_sections = self._find_news_sections(soup)

        if news_sections:
            for section in news_sections:
                articles.extend(self._extract_links_from_section(
                    section, self.base_url, "新着情報",
                ))
        else:
            # セクションが見つからなければページ全体から河川関連リンクを抽出
            articles.extend(self._extract_relevant_links(
                soup, self.base_url, "河川事務所",
            ))

        return articles

    async def _collect_press_page(self) -> list[dict]:
        """記者発表・報道発表ページを探索・収集"""
        articles = []
        soup = await self.fetch_page(self.base_url)
        if not soup:
            return articles

        # 記者発表リンクを探す
        press_urls = set()
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            href = link["href"]
            if any(kw in text for kw in ["記者発表", "報道発表", "プレスリリース"]):
                url = self.resolve_url(href)
                if self._is_same_domain(url):
                    press_urls.add(url)
            # URL パスからも推測
            if any(p in href for p in [
                "press", "kisya", "houdou", "news",
            ]):
                url = self.resolve_url(href)
                if self._is_same_domain(url):
                    press_urls.add(url)

        for url in list(press_urls)[:2]:
            sub_soup = await self.fetch_page(url)
            if sub_soup:
                articles.extend(self._extract_relevant_links(
                    sub_soup, url, "記者発表",
                ))

        return articles

    async def _collect_office_procurement(self) -> list[dict]:
        """河川事務所ごとの入札・発注ページを探索"""
        articles = []
        soup = await self.fetch_page(self.base_url)
        if not soup:
            return articles

        procurement_urls = set()
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            href = link["href"]
            if any(kw in text for kw in [
                "入札", "発注", "契約", "公告", "調達",
            ]):
                url = self.resolve_url(href)
                if self._is_same_domain(url):
                    procurement_urls.add(url)

        for url in list(procurement_urls)[:2]:
            sub_soup = await self.fetch_page(url)
            if sub_soup:
                articles.extend(self._extract_relevant_links(
                    sub_soup, url, "発注情報",
                ))

        return articles

    # --------------------------------------------------
    # ヘルパーメソッド
    # --------------------------------------------------

    def _find_news_sections(self, soup):
        """新着情報セクションをヒューリスティックに探す"""
        sections = []

        # クラス名・id名から探す
        for attr in ["class", "id"]:
            for el in soup.find_all(
                ["div", "section", "ul", "dl", "table"],
                attrs={attr: re.compile(
                    r"(news|topic|whats|info|oshirase|shinchaku|"
                    r"update|kisya|press|announce)",
                    re.I,
                )},
            ):
                sections.append(el)

        # 見出しテキストから探す
        for heading in soup.find_all(["h1", "h2", "h3", "h4"]):
            text = heading.get_text(strip=True)
            if any(kw in text for kw in [
                "新着", "お知らせ", "トピック", "記者発表",
                "報道", "What's New", "NEWS",
            ]):
                parent = heading.find_parent(["div", "section"])
                if parent:
                    sections.append(parent)

        return sections

    def _extract_links_from_section(
        self, section, source_url: str, category: str,
    ) -> list[dict]:
        """セクション内のリンクを記事として抽出"""
        articles = []
        seen_urls = set()

        for link in section.find_all("a", href=True):
            text = link.get_text(strip=True)
            href = link["href"]
            if not text or len(text) < 4:
                continue

            full_url = self.resolve_url(href)
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            # ナビゲーション的なリンクを除外
            if self._is_navigation_link(text, href):
                continue

            date = self._extract_date_from_context(link)
            context = self._get_context_text(link)
            articles.append({
                "source": self.source_name,
                "source_url": source_url,
                "title": text[:200],
                "content": context[:500] if context else None,
                "url": full_url,
                "published_date": date,
                "collected_date": datetime.now().strftime("%Y-%m-%d"),
                "category": category,
                "region": self.region,
            })

        return articles

    def _extract_relevant_links(
        self, soup, source_url: str, category: str,
    ) -> list[dict]:
        """ページ全体から河川事業関連のリンクを抽出"""
        articles = []
        seen_urls = set()

        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            href = link["href"]
            if not text or len(text) < 5:
                continue

            full_url = self.resolve_url(href)
            if full_url in seen_urls:
                continue

            if self._is_navigation_link(text, href):
                continue

            if self._is_relevant(text):
                seen_urls.add(full_url)
                date = self._extract_date_from_context(link)
                context = self._get_context_text(link)
                articles.append({
                    "source": self.source_name,
                    "source_url": source_url,
                    "title": text[:200],
                    "content": context[:500] if context else None,
                    "url": full_url,
                    "published_date": date,
                    "collected_date": datetime.now().strftime("%Y-%m-%d"),
                    "category": category,
                    "region": self.region,
                })

        return articles

    def _get_context_text(self, element) -> str:
        """リンク要素周辺のコンテキストテキストを取得"""
        parent = element.parent
        while parent:
            if parent.name == "tr":
                return parent.get_text(separator=" ", strip=True)
            if parent.name in ("li", "dd", "dt", "p"):
                return parent.get_text(separator=" ", strip=True)
            if parent.name in ("div", "section", "body", "table"):
                break
            parent = parent.parent
        if element.parent:
            return element.parent.get_text(separator=" ", strip=True)[:300]
        return ""

    def _is_relevant(self, text: str) -> bool:
        """河川事業・発注に関連するテキストか判定"""
        keywords = [
            # 河川事業
            "河川", "治水", "洪水", "水害", "浸水", "堤防", "ダム",
            "砂防", "水管理", "流域", "氾濫", "護岸", "水防",
            "整備", "改修", "復旧", "計画", "事業",
            # 技術
            "シミュレーション", "解析", "数値", "計算", "予測",
            "設計", "調査", "測量", "点検", "診断",
            # 発注
            "入札", "公告", "発注", "契約", "業務委託",
            "プロポーザル", "総合評価", "競争入札",
            "工事", "業務",
        ]
        return any(kw in text for kw in keywords)

    def _is_navigation_link(self, text: str, href: str) -> bool:
        """ナビゲーションリンク（トップへ戻る等）かどうか"""
        nav_texts = [
            "トップ", "ホーム", "サイトマップ", "アクセス",
            "リンク集", "問い合わせ", "English", "ページの先頭",
            "戻る", "一覧へ", "前のページ", "次のページ",
            "プライバシー", "著作権", "免責",
        ]
        if any(t in text for t in nav_texts):
            return True
        # 外部リンク（別ドメイン）のうち非政府サイトを除外
        if href.startswith(("javascript:", "mailto:", "#", "tel:")):
            return True
        return False

    def _is_same_domain(self, url: str) -> bool:
        """同一ドメインか判定"""
        base_domain = urlparse(self.base_url).netloc
        target_domain = urlparse(url).netloc
        return base_domain == target_domain

    def _extract_date_from_context(self, element) -> str | None:
        """要素周辺のコンテキストから日付を抽出"""
        # 親要素
        parent = element.parent
        if parent:
            text = parent.get_text()
            date = self.extract_date_from_text(text)
            if date:
                return date

        # 兄弟要素
        for sibling in [element.previous_sibling, element.next_sibling]:
            if sibling and hasattr(sibling, "get_text"):
                date = self.extract_date_from_text(sibling.get_text())
                if date:
                    return date
            elif isinstance(sibling, str):
                date = self.extract_date_from_text(sibling)
                if date:
                    return date

        # dt-dd 構造（よくある日付-記事リスト形式）
        if parent and parent.name == "dd":
            dt = parent.find_previous_sibling("dt")
            if dt:
                date = self.extract_date_from_text(dt.get_text())
                if date:
                    return date

        # tr 内の日付セル
        if parent and parent.name in ("td", "th"):
            row = parent.find_parent("tr")
            if row:
                date = self.extract_date_from_text(row.get_text())
                if date:
                    return date

        return None
