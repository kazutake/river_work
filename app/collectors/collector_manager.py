"""データ収集マネージャー - 全ソースの収集を統括"""

import logging
from datetime import datetime

from ..database import get_db
from ..config import PREFECTURE_SOURCES, REGIONAL_BUREAU_SOURCES
from .mlit_collector import MLITRiverCollector, MLITBureauCollector
from .prefecture_collector import PrefectureCollector

logger = logging.getLogger(__name__)


class CollectorManager:
    """全情報ソースの収集を管理する"""

    def __init__(self):
        self.collectors = []
        self._build_collectors()

    def _build_collectors(self):
        """コレクターを構築"""
        # 国土交通省
        self.collectors.append(MLITRiverCollector())

        # 地方整備局
        for source in REGIONAL_BUREAU_SOURCES:
            self.collectors.append(
                MLITBureauCollector(
                    name=source["name"],
                    url=source["url"],
                    region=source["region"],
                )
            )

        # 都道府県
        for source in PREFECTURE_SOURCES:
            self.collectors.append(
                PrefectureCollector(
                    name=source["name"],
                    url=source["url"],
                    region=source["region"],
                )
            )

    async def run_collection(self) -> dict:
        """全ソースの収集を実行"""
        total_articles = 0
        total_new = 0
        errors = []

        db = await get_db()

        try:
            for collector in self.collectors:
                started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # 収集ログの記録
                await db.execute(
                    "INSERT INTO collection_logs (source, started_at, status) VALUES (?, ?, ?)",
                    (collector.source_name, started_at, "running"),
                )
                await db.commit()
                log_id = (await db.execute("SELECT last_insert_rowid()")).lastrowid

                try:
                    articles = await collector.collect()
                    new_count = 0

                    for article in articles:
                        # 重複チェック（URLベース）
                        existing = await db.execute(
                            "SELECT id FROM articles WHERE url = ?",
                            (article["url"],),
                        )
                        if await existing.fetchone():
                            continue

                        await db.execute(
                            """INSERT INTO articles
                               (source, source_url, title, published_date,
                                collected_date, url, category, region)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (
                                article["source"],
                                article["source_url"],
                                article["title"],
                                article.get("published_date"),
                                article["collected_date"],
                                article["url"],
                                article.get("category"),
                                article.get("region"),
                            ),
                        )
                        new_count += 1

                    await db.commit()
                    total_articles += len(articles)
                    total_new += new_count

                    # ログ更新
                    await db.execute(
                        """UPDATE collection_logs
                           SET finished_at = ?, articles_collected = ?, status = ?
                           WHERE rowid = ?""",
                        (
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            new_count,
                            "completed",
                            log_id,
                        ),
                    )
                    await db.commit()

                    logger.info(
                        f"[{collector.source_name}] 取得: {len(articles)}件, 新規: {new_count}件"
                    )

                except Exception as e:
                    error_msg = f"[{collector.source_name}] エラー: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

                    await db.execute(
                        """UPDATE collection_logs
                           SET finished_at = ?, status = ?, error_message = ?
                           WHERE rowid = ?""",
                        (
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "error",
                            str(e),
                            log_id,
                        ),
                    )
                    await db.commit()

                finally:
                    await collector.close()

        finally:
            await db.close()

        return {
            "total_found": total_articles,
            "total_new": total_new,
            "errors": errors,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
