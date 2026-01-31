"""都道府県 河川関連情報コレクター"""

import logging
import re
from datetime import datetime

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class PrefectureCollector(BaseCollector):
    """都道府県の河川関連ページから情報を収集"""

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

        # ページ内の全リンクを探索
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            href = link["href"]
            if not text or len(text) < 5:
                continue

            # 河川事業に関連するコンテンツをフィルタリング
            if self._is_relevant(text):
                full_url = self.resolve_url(href)
                date = self._extract_date_from_context(link)
                articles.append({
                    "source": self.source_name,
                    "source_url": self.base_url,
                    "title": text[:200],
                    "url": full_url,
                    "published_date": date,
                    "collected_date": datetime.now().strftime("%Y-%m-%d"),
                    "category": "都道府県",
                    "region": self.region,
                })

        # サブページも探索（新着情報リンクなど）
        sub_articles = await self._collect_subpages(soup)
        articles.extend(sub_articles)

        return articles

    async def _collect_subpages(self, main_soup) -> list[dict]:
        """主要なサブページを探索して情報を収集"""
        articles = []

        # 新着情報、お知らせ、事業一覧等のリンクを探す
        subpage_keywords = ["新着", "お知らせ", "事業", "計画", "技術", "報道"]
        subpage_urls = set()

        for link in main_soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            if any(kw in text for kw in subpage_keywords):
                url = self.resolve_url(link["href"])
                # 同一ドメインのみ
                if self._is_same_domain(url):
                    subpage_urls.add(url)

        # 最大3つのサブページを探索
        for url in list(subpage_urls)[:3]:
            soup = await self.fetch_page(url)
            if not soup:
                continue

            for link in soup.find_all("a", href=True):
                text = link.get_text(strip=True)
                href = link["href"]
                if not text or len(text) < 5:
                    continue

                if self._is_relevant(text):
                    full_url = self.resolve_url(href)
                    date = self._extract_date_from_context(link)
                    articles.append({
                        "source": self.source_name,
                        "source_url": url,
                        "title": text[:200],
                        "url": full_url,
                        "published_date": date,
                        "collected_date": datetime.now().strftime("%Y-%m-%d"),
                        "category": "都道府県",
                        "region": self.region,
                    })

        return articles

    def _is_same_domain(self, url: str) -> bool:
        """同一ドメインのURLか判定"""
        from urllib.parse import urlparse
        base_domain = urlparse(self.base_url).netloc
        target_domain = urlparse(url).netloc
        return base_domain == target_domain

    def _is_relevant(self, text: str) -> bool:
        """河川事業に関連するテキストか判定"""
        keywords = [
            "河川", "治水", "洪水", "水害", "浸水", "堤防", "ダム",
            "砂防", "水管理", "流域", "氾濫", "護岸", "水防",
            "シミュレーション", "解析", "数値", "計算", "予測",
            "整備", "計画", "事業", "工事", "調査", "設計",
            "水質", "環境", "生態", "防災", "減災", "災害",
            "改修", "復旧", "耐震", "老朽化", "点検",
        ]
        return any(kw in text for kw in keywords)

    def _extract_date_from_context(self, element) -> str | None:
        """要素の前後から日付を抽出"""
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

        return None
