"""ベースコレクタークラス"""

import httpx
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from abc import ABC, abstractmethod
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en;q=0.9",
}


class BaseCollector(ABC):
    """Webページからの情報収集ベースクラス"""

    def __init__(self, source_name: str, base_url: str, region: str = ""):
        self.source_name = source_name
        self.base_url = base_url
        self.region = region
        self.client = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self.client is None:
            self.client = httpx.AsyncClient(
                headers=HEADERS,
                timeout=30.0,
                follow_redirects=True,
                verify=False,
            )
        return self.client

    async def close(self):
        if self.client:
            await self.client.aclose()
            self.client = None

    async def fetch_page(self, url: str) -> BeautifulSoup | None:
        """ページを取得してBeautifulSoupオブジェクトを返す"""
        try:
            client = await self._get_client()
            response = await client.get(url)
            response.raise_for_status()

            # エンコーディングの自動検出
            content_type = response.headers.get("content-type", "")
            if "charset" in content_type:
                encoding = content_type.split("charset=")[-1].strip()
            else:
                encoding = response.encoding or "utf-8"

            try:
                text = response.content.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                text = response.content.decode("utf-8", errors="replace")

            return BeautifulSoup(text, "html.parser")
        except Exception as e:
            logger.warning(f"ページ取得失敗 [{self.source_name}] {url}: {e}")
            return None

    def resolve_url(self, relative_url: str) -> str:
        """相対URLを絶対URLに変換"""
        if relative_url.startswith(("http://", "https://")):
            return relative_url
        return urljoin(self.base_url, relative_url)

    def extract_date_from_text(self, text: str) -> str | None:
        """テキストから日付を抽出（複数形式対応）"""
        import re
        patterns = [
            r"(\d{4})年(\d{1,2})月(\d{1,2})日",
            r"(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})",
            r"令和(\d{1,2})年(\d{1,2})月(\d{1,2})日",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                if "令和" in pattern:
                    year = int(groups[0]) + 2018
                else:
                    year = int(groups[0])
                month = int(groups[1])
                day = int(groups[2])
                try:
                    return datetime(year, month, day).strftime("%Y-%m-%d")
                except ValueError:
                    continue
        return None

    @abstractmethod
    async def collect(self) -> list[dict]:
        """情報を収集して記事リストを返す"""
        pass
