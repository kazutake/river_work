"""河道計画・河道設計マーケット分析モジュール"""

import logging
from collections import defaultdict

from ..database import get_db
from ..config import KADOU_BUSINESS_CATEGORIES

logger = logging.getLogger(__name__)

# 河道関連記事の判定条件（キーワードテーブル OR 発注詳細テーブルで河道分類あり）
KADOU_FILTER = """(
    a.id IN (
        SELECT article_id FROM keywords
        WHERE keyword_category = '河道計画・河道設計'
    )
    OR a.id IN (
        SELECT article_id FROM procurement_details
        WHERE kadou_category IS NOT NULL
    )
)"""


class MarketAnalyzer:
    """河道計画・設計業務のマーケット規模・ニーズを分析する"""

    # --------------------------------------------------
    # 1. マーケット規模サマリー
    # --------------------------------------------------
    async def get_market_summary(self, period: str = "all") -> dict:
        """河道計画・設計関連のマーケット規模サマリーを返す"""
        db = await get_db()
        try:
            cond = self._period_condition(period)

            # 河道関連記事の発注詳細を集計
            cursor = await db.execute(f"""
                SELECT
                    COUNT(DISTINCT a.id) as total_projects,
                    COUNT(DISTINCT CASE WHEN pd.estimated_amount IS NOT NULL
                                        THEN a.id END) as with_est,
                    COUNT(DISTINCT CASE WHEN pd.contract_amount IS NOT NULL
                                        THEN a.id END) as with_contract,
                    SUM(CASE WHEN pd.contract_amount IS NOT NULL
                         THEN pd.contract_amount
                         ELSE pd.estimated_amount END) as total_amount,
                    AVG(CASE WHEN pd.contract_amount IS NOT NULL
                         THEN pd.contract_amount
                         WHEN pd.estimated_amount IS NOT NULL
                         THEN pd.estimated_amount END) as avg_amount
                FROM articles a
                LEFT JOIN procurement_details pd ON a.id = pd.article_id
                WHERE {cond}
                  AND {KADOU_FILTER}
            """)
            row = await cursor.fetchone()

            # 業務委託 vs 工事の内訳
            type_cursor = await db.execute(f"""
                SELECT
                    COALESCE(pd.business_type, '未分類') as btype,
                    COUNT(DISTINCT a.id) as count,
                    SUM(CASE WHEN pd.contract_amount IS NOT NULL
                         THEN pd.contract_amount
                         ELSE pd.estimated_amount END) as total,
                    AVG(CASE WHEN pd.contract_amount IS NOT NULL
                         THEN pd.contract_amount
                         WHEN pd.estimated_amount IS NOT NULL
                         THEN pd.estimated_amount END) as avg
                FROM articles a
                LEFT JOIN procurement_details pd ON a.id = pd.article_id
                WHERE {cond}
                  AND {KADOU_FILTER}
                GROUP BY btype
                ORDER BY count DESC
            """)
            type_rows = await type_cursor.fetchall()

            projects_with_amount = (row[1] or 0) + (row[2] or 0)
            # 重複を除くため max
            projects_with_amount = min(projects_with_amount, row[0] or 0)

            return {
                "total_projects": row[0] or 0,
                "projects_with_amount": projects_with_amount,
                "total_amount": row[3] or 0,
                "avg_amount": int(row[4]) if row[4] else 0,
                "by_business_type": [
                    {
                        "type": r[0],
                        "count": r[1],
                        "total_amount": r[2] or 0,
                        "avg_amount": int(r[3]) if r[3] else 0,
                    }
                    for r in type_rows
                ],
                "period": period,
            }
        finally:
            await db.close()

    # --------------------------------------------------
    # 2. 河道業務カテゴリ別の分析
    # --------------------------------------------------
    async def get_kadou_category_breakdown(self, period: str = "all") -> list[dict]:
        """河道計画・設計の業務サブカテゴリ別集計"""
        db = await get_db()
        try:
            cond = self._period_condition(period)

            # procurement_details.kadou_category を使った集計
            cursor = await db.execute(f"""
                SELECT
                    pd.kadou_category,
                    COUNT(DISTINCT a.id) as count,
                    SUM(CASE WHEN pd.contract_amount IS NOT NULL
                         THEN pd.contract_amount
                         ELSE pd.estimated_amount END) as total_amount,
                    AVG(CASE WHEN pd.contract_amount IS NOT NULL
                         THEN pd.contract_amount
                         WHEN pd.estimated_amount IS NOT NULL
                         THEN pd.estimated_amount END) as avg_amount
                FROM articles a
                JOIN procurement_details pd ON a.id = pd.article_id
                WHERE {cond}
                  AND pd.kadou_category IS NOT NULL
                GROUP BY pd.kadou_category
                ORDER BY count DESC
            """)
            rows = await cursor.fetchall()

            result = [
                {
                    "category": row[0],
                    "count": row[1],
                    "total_amount": row[2] or 0,
                    "avg_amount": int(row[3]) if row[3] else 0,
                }
                for row in rows
            ]

            # キーワードテーブルからも補完（procurement_detailsに未分類でも
            # キーワードで河道関連と判定された記事のキーワード頻度）
            if not result:
                kw_cursor = await db.execute(f"""
                    SELECT k.keyword, COUNT(DISTINCT a.id) as count
                    FROM articles a
                    JOIN keywords k ON a.id = k.article_id
                    WHERE {cond}
                      AND k.keyword_category = '河道計画・河道設計'
                    GROUP BY k.keyword
                    ORDER BY count DESC
                    LIMIT 10
                """)
                kw_rows = await kw_cursor.fetchall()
                result = [
                    {"category": row[0], "count": row[1],
                     "total_amount": 0, "avg_amount": 0}
                    for row in kw_rows
                ]

            return result
        finally:
            await db.close()

    # --------------------------------------------------
    # 3. ニーズ分析（どんなキーワードが発注情報に多いか）
    # --------------------------------------------------
    async def get_needs_analysis(self, period: str = "all") -> dict:
        """河道計画・設計に関わるニーズ分析"""
        db = await get_db()
        try:
            cond = self._period_condition(period)

            # 河道関連記事に同時に出現する他カテゴリキーワードを集計
            cursor = await db.execute(f"""
                SELECT k.keyword, k.keyword_category,
                       COUNT(DISTINCT a.id) as article_count,
                       SUM(k.frequency) as total_freq
                FROM articles a
                JOIN keywords k ON a.id = k.article_id
                WHERE {cond}
                  AND {KADOU_FILTER}
                  AND k.keyword_category != '河道計画・河道設計'
                GROUP BY k.keyword, k.keyword_category
                ORDER BY article_count DESC
                LIMIT 30
            """)
            co_keywords = [
                {
                    "keyword": row[0],
                    "category": row[1],
                    "article_count": row[2],
                    "frequency": row[3],
                }
                for row in await cursor.fetchall()
            ]

            # 河道関連記事内で最も頻出する河道計画・設計キーワード
            kadou_cursor = await db.execute(f"""
                SELECT k.keyword, SUM(k.frequency) as total,
                       COUNT(DISTINCT a.id) as article_count
                FROM keywords k
                JOIN articles a ON k.article_id = a.id
                WHERE {cond}
                  AND k.keyword_category = '河道計画・河道設計'
                GROUP BY k.keyword
                ORDER BY total DESC
            """)
            kadou_keywords = [
                {
                    "keyword": row[0],
                    "frequency": row[1],
                    "article_count": row[2],
                }
                for row in await kadou_cursor.fetchall()
            ]

            return {
                "kadou_keywords": kadou_keywords,
                "co_occurring_keywords": co_keywords,
            }
        finally:
            await db.close()

    # --------------------------------------------------
    # 4. 求められる技術の分析
    # --------------------------------------------------
    async def get_technology_demand(self, period: str = "all") -> dict:
        """河道計画・設計で求められている技術の分析"""
        db = await get_db()
        try:
            cond = self._period_condition(period)

            # 河道関連記事に出現する「数値解析・シミュレーション」と「先端技術」
            tech_cursor = await db.execute(f"""
                SELECT k.keyword, k.keyword_category,
                       COUNT(DISTINCT a.id) as article_count,
                       SUM(k.frequency) as total_freq
                FROM articles a
                JOIN keywords k ON a.id = k.article_id
                WHERE {cond}
                  AND {KADOU_FILTER}
                  AND k.keyword_category IN (
                      '数値解析・シミュレーション', '先端技術'
                  )
                GROUP BY k.keyword, k.keyword_category
                ORDER BY article_count DESC
            """)
            tech_keywords = [
                {
                    "keyword": row[0],
                    "category": row[1],
                    "article_count": row[2],
                    "frequency": row[3],
                }
                for row in await tech_cursor.fetchall()
            ]

            # 入札方式別の件数
            method_cursor = await db.execute(f"""
                SELECT pd.procurement_method, COUNT(DISTINCT a.id) as count
                FROM articles a
                JOIN procurement_details pd ON a.id = pd.article_id
                WHERE {cond}
                  AND {KADOU_FILTER}
                  AND pd.procurement_method IS NOT NULL
                GROUP BY pd.procurement_method
                ORDER BY count DESC
            """)
            methods = [
                {"method": row[0], "count": row[1]}
                for row in await method_cursor.fetchall()
            ]

            return {
                "technology_keywords": tech_keywords,
                "procurement_methods": methods,
            }
        finally:
            await db.close()

    # --------------------------------------------------
    # 5. 地域別マーケット
    # --------------------------------------------------
    async def get_regional_market(self, period: str = "all") -> list[dict]:
        """地域別の河道計画・設計マーケット"""
        db = await get_db()
        try:
            cond = self._period_condition(period)
            cursor = await db.execute(f"""
                SELECT a.region,
                       COUNT(DISTINCT a.id) as project_count,
                       SUM(CASE WHEN pd.contract_amount IS NOT NULL
                            THEN pd.contract_amount
                            ELSE pd.estimated_amount END) as total_amount,
                       AVG(CASE WHEN pd.contract_amount IS NOT NULL
                            THEN pd.contract_amount
                            WHEN pd.estimated_amount IS NOT NULL
                            THEN pd.estimated_amount END) as avg_amount
                FROM articles a
                LEFT JOIN procurement_details pd ON a.id = pd.article_id
                WHERE {cond}
                  AND {KADOU_FILTER}
                  AND a.region IS NOT NULL
                GROUP BY a.region
                ORDER BY project_count DESC
            """)
            return [
                {
                    "region": row[0],
                    "project_count": row[1],
                    "total_amount": row[2] or 0,
                    "avg_amount": int(row[3]) if row[3] else 0,
                }
                for row in await cursor.fetchall()
            ]
        finally:
            await db.close()

    # --------------------------------------------------
    # 6. 発注案件一覧（河道関連）
    # --------------------------------------------------
    async def get_kadou_projects(
        self, period: str = "all", page: int = 1, per_page: int = 20,
    ) -> dict:
        """河道計画・設計関連の発注案件一覧"""
        db = await get_db()
        try:
            cond = self._period_condition(period)

            count_cursor = await db.execute(f"""
                SELECT COUNT(DISTINCT a.id)
                FROM articles a
                WHERE {cond}
                  AND {KADOU_FILTER}
            """)
            total = (await count_cursor.fetchone())[0]

            offset = (page - 1) * per_page
            cursor = await db.execute(f"""
                SELECT DISTINCT a.id, a.source, a.title, a.url,
                       a.published_date, a.collected_date, a.region,
                       pd.estimated_amount, pd.contract_amount,
                       pd.business_type, pd.procurement_method,
                       pd.kadou_category
                FROM articles a
                LEFT JOIN procurement_details pd ON a.id = pd.article_id
                WHERE {cond}
                  AND {KADOU_FILTER}
                ORDER BY a.collected_date DESC
                LIMIT ? OFFSET ?
            """, (per_page, offset))
            rows = await cursor.fetchall()

            return {
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page if total else 0,
                "projects": [
                    {
                        "id": r[0],
                        "source": r[1],
                        "title": r[2],
                        "url": r[3],
                        "published_date": r[4],
                        "collected_date": r[5],
                        "region": r[6],
                        "estimated_amount": r[7],
                        "contract_amount": r[8],
                        "business_type": r[9],
                        "procurement_method": r[10],
                        "kadou_category": r[11],
                    }
                    for r in rows
                ],
            }
        finally:
            await db.close()

    # --------------------------------------------------
    def _period_condition(self, period: str) -> str:
        mapping = {
            "7d": "DATE(a.collected_date) >= DATE('now', '-7 days')",
            "30d": "DATE(a.collected_date) >= DATE('now', '-30 days')",
            "90d": "DATE(a.collected_date) >= DATE('now', '-90 days')",
            "180d": "DATE(a.collected_date) >= DATE('now', '-180 days')",
            "365d": "DATE(a.collected_date) >= DATE('now', '-365 days')",
            "all": "1=1",
        }
        return mapping.get(period, mapping["all"])
