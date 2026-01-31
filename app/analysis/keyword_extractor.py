"""キーワード抽出・分析モジュール"""

import re
import logging
from collections import Counter
from datetime import datetime

from ..config import RIVER_KEYWORDS
from ..database import get_db

logger = logging.getLogger(__name__)


class KeywordExtractor:
    """記事タイトル・本文からキーワードを抽出して分類する"""

    def __init__(self):
        # フラットなキーワード→カテゴリのマッピングを構築
        self.keyword_to_category = {}
        for category, keywords in RIVER_KEYWORDS.items():
            for kw in keywords:
                self.keyword_to_category[kw] = category

        # 長いキーワードを先にマッチさせるためソート
        self.sorted_keywords = sorted(
            self.keyword_to_category.keys(), key=len, reverse=True
        )

    def extract_keywords(self, text: str) -> list[dict]:
        """テキストからキーワードを抽出"""
        if not text:
            return []

        found = []
        text_lower = text.lower()

        for keyword in self.sorted_keywords:
            keyword_lower = keyword.lower()
            count = text_lower.count(keyword_lower)
            if count > 0:
                found.append({
                    "keyword": keyword,
                    "category": self.keyword_to_category[keyword],
                    "frequency": count,
                })

        return found

    async def analyze_articles(self):
        """未解析の記事のキーワードを抽出してDBに保存"""
        db = await get_db()
        try:
            # キーワード未抽出の記事を取得
            cursor = await db.execute(
                """SELECT a.id, a.title, a.content
                   FROM articles a
                   LEFT JOIN keywords k ON a.id = k.article_id
                   WHERE k.id IS NULL"""
            )
            articles = await cursor.fetchall()

            count = 0
            for article in articles:
                text = (article[1] or "") + " " + (article[2] or "")
                keywords = self.extract_keywords(text)

                for kw in keywords:
                    await db.execute(
                        """INSERT INTO keywords (article_id, keyword, keyword_category, frequency)
                           VALUES (?, ?, ?, ?)""",
                        (article[0], kw["keyword"], kw["category"], kw["frequency"]),
                    )
                    count += 1

            await db.commit()
            logger.info(f"キーワード抽出完了: {len(articles)}記事, {count}キーワード")
            return {"articles_processed": len(articles), "keywords_extracted": count}
        finally:
            await db.close()

    async def generate_trend_snapshot(self):
        """トレンドスナップショットを生成"""
        db = await get_db()
        try:
            today = datetime.now().strftime("%Y-%m-%d")

            # 各期間でのキーワード集計
            periods = {
                "7d": "DATE(collected_date) >= DATE('now', '-7 days')",
                "30d": "DATE(collected_date) >= DATE('now', '-30 days')",
                "90d": "DATE(collected_date) >= DATE('now', '-90 days')",
                "all": "1=1",
            }

            for period_name, condition in periods.items():
                cursor = await db.execute(f"""
                    SELECT k.keyword, k.keyword_category, SUM(k.frequency) as total
                    FROM keywords k
                    JOIN articles a ON k.article_id = a.id
                    WHERE {condition}
                    GROUP BY k.keyword, k.keyword_category
                    ORDER BY total DESC
                """)
                rows = await cursor.fetchall()

                for row in rows:
                    await db.execute(
                        """INSERT INTO trend_snapshots
                           (snapshot_date, keyword, keyword_category, count, period)
                           VALUES (?, ?, ?, ?, ?)""",
                        (today, row[0], row[1], row[2], period_name),
                    )

            await db.commit()
            logger.info(f"トレンドスナップショット生成完了: {today}")
        finally:
            await db.close()
