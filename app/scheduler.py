"""定期実行スケジューラー"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .collectors.collector_manager import CollectorManager
from .analysis.keyword_extractor import KeywordExtractor

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def daily_collection_job():
    """日次データ収集ジョブ"""
    logger.info("日次データ収集ジョブ開始")
    try:
        manager = CollectorManager()
        result = await manager.run_collection()
        logger.info(f"収集完了: {result}")

        extractor = KeywordExtractor()
        await extractor.analyze_articles()
        await extractor.generate_trend_snapshot()
        logger.info("キーワード解析・トレンドスナップショット完了")
    except Exception as e:
        logger.error(f"日次ジョブエラー: {e}")


def start_scheduler():
    """スケジューラーを開始"""
    # 毎日6:00にデータ収集を実行
    scheduler.add_job(
        daily_collection_job,
        "cron",
        hour=6,
        minute=0,
        id="daily_collection",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("スケジューラー起動: 毎日06:00にデータ収集を実行")


def stop_scheduler():
    """スケジューラーを停止"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("スケジューラー停止")
