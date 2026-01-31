"""国土交通省 河川関連情報コレクター"""

import logging
import re
from datetime import datetime
from urllib.parse import urljoin

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class MLITRiverCollector(BaseCollector):
    """国土交通省 水管理・国土保全局のページから情報を収集"""

    def __init__(self):
        super().__init__(
            source_name="国土交通省 水管理・国土保全局",
            base_url="https://www.mlit.go.jp/river/",
            region="全国",
        )

    async def collect(self) -> list[dict]:
        articles = []

        # 報道発表・お知らせページ
        articles.extend(await self._collect_press_releases())

        # 技術基準・ガイドライン
        articles.extend(await self._collect_technical_standards())

        # 河川砂防技術研究開発
        articles.extend(await self._collect_research())

        # トピックス・新着情報
        articles.extend(await self._collect_topics())

        return articles

    async def _collect_press_releases(self) -> list[dict]:
        """報道発表の収集"""
        articles = []
        url = "https://www.mlit.go.jp/river/river_tk1_000014.html"
        soup = await self.fetch_page(url)
        if not soup:
            return articles

        # リンク一覧から報道発表を抽出
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            href = link["href"]
            if not text or len(text) < 5:
                continue

            # 河川関連のキーワードでフィルタリング
            if self._is_river_related(text):
                full_url = self.resolve_url(href)
                date = self._extract_date_from_context(link)
                articles.append({
                    "source": self.source_name,
                    "source_url": url,
                    "title": text[:200],
                    "url": full_url,
                    "published_date": date,
                    "collected_date": datetime.now().strftime("%Y-%m-%d"),
                    "category": "報道発表",
                    "region": self.region,
                })

        return articles

    async def _collect_technical_standards(self) -> list[dict]:
        """技術基準・ガイドラインの収集"""
        articles = []
        url = "https://www.mlit.go.jp/river/shishin_guideline/index.html"
        soup = await self.fetch_page(url)
        if not soup:
            return articles

        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            href = link["href"]
            if not text or len(text) < 5:
                continue

            if self._is_river_related(text) or self._is_technical(text):
                full_url = self.resolve_url(href)
                date = self._extract_date_from_context(link)
                articles.append({
                    "source": self.source_name,
                    "source_url": url,
                    "title": text[:200],
                    "url": full_url,
                    "published_date": date,
                    "collected_date": datetime.now().strftime("%Y-%m-%d"),
                    "category": "技術基準",
                    "region": self.region,
                })

        return articles

    async def _collect_research(self) -> list[dict]:
        """河川砂防技術研究開発の収集"""
        articles = []
        url = "https://www.mlit.go.jp/river/gijutsu/index.html"
        soup = await self.fetch_page(url)
        if not soup:
            return articles

        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            href = link["href"]
            if not text or len(text) < 5:
                continue

            full_url = self.resolve_url(href)
            date = self._extract_date_from_context(link)
            articles.append({
                "source": self.source_name,
                "source_url": url,
                "title": text[:200],
                "url": full_url,
                "published_date": date,
                "collected_date": datetime.now().strftime("%Y-%m-%d"),
                "category": "技術研究開発",
                "region": self.region,
            })

        return articles

    async def _collect_topics(self) -> list[dict]:
        """トップページの新着情報の収集"""
        articles = []
        url = "https://www.mlit.go.jp/river/index.html"
        soup = await self.fetch_page(url)
        if not soup:
            return articles

        # 新着情報やトピックスセクションの探索
        for section in soup.find_all(["div", "ul", "dl"], class_=re.compile(
            r"(news|topic|whats|info|update)", re.I
        )):
            for link in section.find_all("a", href=True):
                text = link.get_text(strip=True)
                href = link["href"]
                if not text or len(text) < 5:
                    continue

                full_url = self.resolve_url(href)
                date = self._extract_date_from_context(link)
                articles.append({
                    "source": self.source_name,
                    "source_url": url,
                    "title": text[:200],
                    "url": full_url,
                    "published_date": date,
                    "collected_date": datetime.now().strftime("%Y-%m-%d"),
                    "category": "新着情報",
                    "region": self.region,
                })

        return articles

    def _extract_date_from_context(self, element) -> str | None:
        """要素の前後のコンテキストから日付を抽出"""
        # 親要素のテキストから日付を探す
        parent = element.parent
        if parent:
            text = parent.get_text()
            date = self.extract_date_from_text(text)
            if date:
                return date

        # 兄弟要素を探索
        for sibling in [element.previous_sibling, element.next_sibling]:
            if sibling and hasattr(sibling, "get_text"):
                date = self.extract_date_from_text(sibling.get_text())
                if date:
                    return date
            elif isinstance(sibling, str):
                date = self.extract_date_from_text(sibling)
                if date:
                    return date

        return None

    def _is_river_related(self, text: str) -> bool:
        """河川事業に関連するテキストか判定"""
        keywords = [
            "河川", "治水", "洪水", "水害", "浸水", "堤防", "ダム",
            "砂防", "水管理", "流域", "氾濫", "護岸", "水防",
            "水質", "水環境", "河道", "遊水", "放水路", "排水",
        ]
        return any(kw in text for kw in keywords)

    def _is_technical(self, text: str) -> bool:
        """技術関連のテキストか判定"""
        keywords = [
            "技術", "基準", "ガイドライン", "マニュアル", "計算",
            "シミュレーション", "解析", "設計", "施工", "調査",
        ]
        return any(kw in text for kw in keywords)


class MLITBureauCollector(BaseCollector):
    """地方整備局の河川情報を収集"""

    def __init__(self, name: str, url: str, region: str):
        super().__init__(
            source_name=name,
            base_url=url,
            region=region,
        )

    async def collect(self) -> list[dict]:
        articles = []
        soup = await self.fetch_page(self.base_url)
        if not soup:
            return articles

        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            href = link["href"]
            if not text or len(text) < 5:
                continue

            # 河川関連コンテンツのフィルタリング
            keywords = [
                "河川", "治水", "洪水", "水害", "ダム", "砂防",
                "シミュレーション", "解析", "予測", "技術",
                "整備", "計画", "事業", "工事", "調査",
            ]
            if any(kw in text for kw in keywords):
                full_url = self.resolve_url(href)
                date_text = self._extract_date_from_context(link)
                articles.append({
                    "source": self.source_name,
                    "source_url": self.base_url,
                    "title": text[:200],
                    "url": full_url,
                    "published_date": date_text,
                    "collected_date": datetime.now().strftime("%Y-%m-%d"),
                    "category": "地方整備局",
                    "region": self.region,
                })

        return articles

    def _extract_date_from_context(self, element) -> str | None:
        parent = element.parent
        if parent:
            text = parent.get_text()
            date = self.extract_date_from_text(text)
            if date:
                return date
        return None
