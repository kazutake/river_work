"""トレンド分析モジュール"""

import logging
from datetime import datetime, timedelta
from collections import defaultdict

from ..database import get_db

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """収集データからトレンドを分析する"""

    async def get_keyword_trends(
        self, period: str = "30d", category: str | None = None, limit: int = 20
    ) -> list[dict]:
        """キーワードのトレンドランキングを取得"""
        db = await get_db()
        try:
            condition = self._period_condition(period)
            params = []

            query = f"""
                SELECT k.keyword, k.keyword_category, SUM(k.frequency) as total,
                       COUNT(DISTINCT k.article_id) as article_count
                FROM keywords k
                JOIN articles a ON k.article_id = a.id
                WHERE {condition}
                  AND k.keyword != '_none_'
            """

            if category:
                query += " AND k.keyword_category = ?"
                params.append(category)

            query += " GROUP BY k.keyword, k.keyword_category ORDER BY total DESC LIMIT ?"
            params.append(limit)

            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()

            return [
                {
                    "keyword": row[0],
                    "category": row[1],
                    "total_frequency": row[2],
                    "article_count": row[3],
                }
                for row in rows
            ]
        finally:
            await db.close()

    async def get_category_distribution(self, period: str = "30d") -> list[dict]:
        """カテゴリ別の分布を取得"""
        db = await get_db()
        try:
            condition = self._period_condition(period)
            cursor = await db.execute(f"""
                SELECT k.keyword_category, SUM(k.frequency) as total,
                       COUNT(DISTINCT k.article_id) as article_count
                FROM keywords k
                JOIN articles a ON k.article_id = a.id
                WHERE {condition}
                  AND k.keyword != '_none_'
                GROUP BY k.keyword_category
                ORDER BY total DESC
            """)
            rows = await cursor.fetchall()

            return [
                {
                    "category": row[0],
                    "total_frequency": row[1],
                    "article_count": row[2],
                }
                for row in rows
            ]
        finally:
            await db.close()

    async def get_time_series(
        self, keywords: list[str] | None = None, period: str = "90d"
    ) -> dict:
        """キーワードの時系列推移を取得"""
        db = await get_db()
        try:
            condition = self._period_condition(period)

            if keywords:
                placeholders = ",".join(["?"] * len(keywords))
                keyword_filter = f"AND k.keyword IN ({placeholders})"
                params = keywords
            else:
                # トップ10キーワードを自動選択
                keyword_filter = ""
                params = []

                top_cursor = await db.execute(f"""
                    SELECT k.keyword
                    FROM keywords k
                    JOIN articles a ON k.article_id = a.id
                    WHERE {condition}
                      AND k.keyword != '_none_'
                    GROUP BY k.keyword
                    ORDER BY SUM(k.frequency) DESC
                    LIMIT 10
                """)
                top_rows = await top_cursor.fetchall()
                keywords = [row[0] for row in top_rows]
                if keywords:
                    placeholders = ",".join(["?"] * len(keywords))
                    keyword_filter = f"AND k.keyword IN ({placeholders})"
                    params = keywords

            cursor = await db.execute(f"""
                SELECT DATE(a.collected_date) as date,
                       k.keyword,
                       SUM(k.frequency) as count
                FROM keywords k
                JOIN articles a ON k.article_id = a.id
                WHERE {condition}
                  AND k.keyword != '_none_'
                  {keyword_filter}
                GROUP BY DATE(a.collected_date), k.keyword
                ORDER BY date
            """, params)
            rows = await cursor.fetchall()

            # 時系列データの整形
            series = defaultdict(list)
            dates = sorted(set(row[0] for row in rows))

            for keyword in (keywords or []):
                keyword_data = {row[0]: row[2] for row in rows if row[1] == keyword}
                series[keyword] = [
                    {"date": d, "count": keyword_data.get(d, 0)} for d in dates
                ]

            return {"dates": dates, "series": dict(series)}
        finally:
            await db.close()

    async def get_simulation_trends(self, period: str = "90d") -> dict:
        """数値解析・シミュレーション関連のトレンド詳細"""
        db = await get_db()
        try:
            condition = self._period_condition(period)
            cursor = await db.execute(f"""
                SELECT k.keyword, SUM(k.frequency) as total,
                       COUNT(DISTINCT k.article_id) as article_count,
                       COUNT(DISTINCT a.source) as source_count
                FROM keywords k
                JOIN articles a ON k.article_id = a.id
                WHERE {condition}
                  AND k.keyword_category = '数値解析・シミュレーション'
                  AND k.keyword != '_none_'
                GROUP BY k.keyword
                ORDER BY total DESC
            """)
            rows = await cursor.fetchall()

            return {
                "keywords": [
                    {
                        "keyword": row[0],
                        "total_frequency": row[1],
                        "article_count": row[2],
                        "source_count": row[3],
                    }
                    for row in rows
                ],
                "period": period,
            }
        finally:
            await db.close()

    async def get_regional_analysis(self, period: str = "30d") -> list[dict]:
        """地域別の分析"""
        db = await get_db()
        try:
            condition = self._period_condition(period)
            cursor = await db.execute(f"""
                SELECT a.region,
                       COUNT(DISTINCT a.id) as article_count,
                       k.keyword_category,
                       SUM(k.frequency) as total
                FROM articles a
                JOIN keywords k ON a.id = k.article_id
                WHERE {condition}
                  AND a.region IS NOT NULL
                  AND k.keyword != '_none_'
                GROUP BY a.region, k.keyword_category
                ORDER BY a.region, total DESC
            """)
            rows = await cursor.fetchall()

            # 地域別にグループ化
            regional = defaultdict(lambda: {"article_count": 0, "categories": {}})
            for row in rows:
                region = row[0]
                regional[region]["article_count"] = max(
                    regional[region]["article_count"], row[1]
                )
                regional[region]["categories"][row[2]] = row[3]

            return [
                {
                    "region": region,
                    "article_count": data["article_count"],
                    "categories": data["categories"],
                }
                for region, data in sorted(regional.items())
            ]
        finally:
            await db.close()

    async def get_dashboard_summary(self) -> dict:
        """ダッシュボード用のサマリーデータ"""
        db = await get_db()
        try:
            # 記事総数
            total_cursor = await db.execute("SELECT COUNT(*) FROM articles")
            total_articles = (await total_cursor.fetchone())[0]

            # 今日の収集数
            today_cursor = await db.execute(
                "SELECT COUNT(*) FROM articles WHERE collected_date = DATE('now')"
            )
            today_articles = (await today_cursor.fetchone())[0]

            # ソース数
            source_cursor = await db.execute(
                "SELECT COUNT(DISTINCT source) FROM articles"
            )
            total_sources = (await source_cursor.fetchone())[0]

            # 直近7日間のトップキーワード
            top_cursor = await db.execute("""
                SELECT k.keyword, k.keyword_category, SUM(k.frequency) as total
                FROM keywords k
                JOIN articles a ON k.article_id = a.id
                WHERE DATE(a.collected_date) >= DATE('now', '-7 days')
                  AND k.keyword != '_none_'
                GROUP BY k.keyword
                ORDER BY total DESC
                LIMIT 10
            """)
            top_keywords = [
                {"keyword": row[0], "category": row[1], "count": row[2]}
                for row in await top_cursor.fetchall()
            ]

            # 直近の収集ログ
            log_cursor = await db.execute("""
                SELECT source, started_at, articles_collected, status
                FROM collection_logs
                ORDER BY started_at DESC
                LIMIT 10
            """)
            recent_logs = [
                {
                    "source": row[0],
                    "started_at": row[1],
                    "articles_collected": row[2],
                    "status": row[3],
                }
                for row in await log_cursor.fetchall()
            ]

            return {
                "total_articles": total_articles,
                "today_articles": today_articles,
                "total_sources": total_sources,
                "top_keywords": top_keywords,
                "recent_logs": recent_logs,
            }
        finally:
            await db.close()

    def _period_condition(self, period: str) -> str:
        """期間条件のSQL生成"""
        mapping = {
            "7d": "DATE(a.collected_date) >= DATE('now', '-7 days')",
            "30d": "DATE(a.collected_date) >= DATE('now', '-30 days')",
            "90d": "DATE(a.collected_date) >= DATE('now', '-90 days')",
            "180d": "DATE(a.collected_date) >= DATE('now', '-180 days')",
            "365d": "DATE(a.collected_date) >= DATE('now', '-365 days')",
            "all": "1=1",
        }
        return mapping.get(period, mapping["30d"])
