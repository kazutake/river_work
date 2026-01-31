"""河川事業トレンド分析アプリケーション - メインエントリポイント"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse

from .database import init_db
from .analysis.keyword_extractor import KeywordExtractor
from .analysis.trend_analyzer import TrendAnalyzer
from .collectors.collector_manager import CollectorManager
from .scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    logger.info("河川事業トレンド分析アプリケーション起動中...")
    await init_db()
    start_scheduler()
    logger.info("起動完了")
    yield
    stop_scheduler()
    logger.info("シャットダウン完了")


app = FastAPI(
    title="河川事業トレンド分析",
    description="国土交通省・都道府県の河川事業情報を収集・分析し、トレンドを可視化するアプリケーション",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

trend_analyzer = TrendAnalyzer()
keyword_extractor = KeywordExtractor()


# === HTMLページ ===

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """メインダッシュボード"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


# === API エンドポイント ===

@app.get("/api/summary")
async def api_summary():
    """ダッシュボードサマリー"""
    return await trend_analyzer.get_dashboard_summary()


@app.get("/api/trends/keywords")
async def api_keyword_trends(
    period: str = Query("30d", regex=r"^(7d|30d|90d|180d|365d|all)$"),
    category: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """キーワードトレンドランキング"""
    return await trend_analyzer.get_keyword_trends(period, category, limit)


@app.get("/api/trends/categories")
async def api_category_distribution(
    period: str = Query("30d", regex=r"^(7d|30d|90d|180d|365d|all)$"),
):
    """カテゴリ別分布"""
    return await trend_analyzer.get_category_distribution(period)


@app.get("/api/trends/timeseries")
async def api_time_series(
    period: str = Query("90d", regex=r"^(7d|30d|90d|180d|365d|all)$"),
    keywords: str | None = Query(None, description="カンマ区切りキーワード"),
):
    """キーワード時系列推移"""
    kw_list = keywords.split(",") if keywords else None
    return await trend_analyzer.get_time_series(kw_list, period)


@app.get("/api/trends/simulation")
async def api_simulation_trends(
    period: str = Query("90d", regex=r"^(7d|30d|90d|180d|365d|all)$"),
):
    """数値解析・シミュレーション関連トレンド"""
    return await trend_analyzer.get_simulation_trends(period)


@app.get("/api/trends/regional")
async def api_regional_analysis(
    period: str = Query("30d", regex=r"^(7d|30d|90d|180d|365d|all)$"),
):
    """地域別分析"""
    return await trend_analyzer.get_regional_analysis(period)


@app.get("/api/articles")
async def api_articles(
    period: str = Query("30d", regex=r"^(7d|30d|90d|180d|365d|all)$"),
    category: str | None = Query(None),
    region: str | None = Query(None),
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """記事一覧"""
    from .database import get_db

    db = await get_db()
    try:
        conditions = []
        params = []

        period_map = {
            "7d": "-7 days", "30d": "-30 days", "90d": "-90 days",
            "180d": "-180 days", "365d": "-365 days",
        }
        if period != "all" and period in period_map:
            conditions.append(f"DATE(a.collected_date) >= DATE('now', ?)")
            params.append(period_map[period])

        if category:
            conditions.append("a.category = ?")
            params.append(category)

        if region:
            conditions.append("a.region = ?")
            params.append(region)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        if keyword:
            if where:
                where += " AND a.id IN (SELECT article_id FROM keywords WHERE keyword = ?)"
            else:
                where = "WHERE a.id IN (SELECT article_id FROM keywords WHERE keyword = ?)"
            params.append(keyword)

        # 総数
        count_cursor = await db.execute(
            f"SELECT COUNT(*) FROM articles a {where}", params
        )
        total = (await count_cursor.fetchone())[0]

        # ページネーション
        offset = (page - 1) * per_page
        cursor = await db.execute(
            f"""SELECT a.id, a.source, a.title, a.published_date,
                       a.collected_date, a.url, a.category, a.region
                FROM articles a {where}
                ORDER BY a.collected_date DESC, a.id DESC
                LIMIT ? OFFSET ?""",
            params + [per_page, offset],
        )
        rows = await cursor.fetchall()

        articles = [
            {
                "id": row[0],
                "source": row[1],
                "title": row[2],
                "published_date": row[3],
                "collected_date": row[4],
                "url": row[5],
                "category": row[6],
                "region": row[7],
            }
            for row in rows
        ]

        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
            "articles": articles,
        }
    finally:
        await db.close()


@app.post("/api/collect")
async def api_trigger_collection(background_tasks: BackgroundTasks):
    """手動でデータ収集をトリガー"""
    async def run():
        manager = CollectorManager()
        result = await manager.run_collection()
        logger.info(f"手動収集完了: {result}")
        # 収集後にキーワード解析を実行
        await keyword_extractor.analyze_articles()
        await keyword_extractor.generate_trend_snapshot()

    background_tasks.add_task(run)
    return {"status": "collecting", "message": "データ収集を開始しました"}


@app.get("/api/collection/logs")
async def api_collection_logs(limit: int = Query(20, ge=1, le=100)):
    """収集ログの取得"""
    from .database import get_db

    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT source, started_at, finished_at, articles_collected, status, error_message
               FROM collection_logs
               ORDER BY started_at DESC
               LIMIT ?""",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "source": row[0],
                "started_at": row[1],
                "finished_at": row[2],
                "articles_collected": row[3],
                "status": row[4],
                "error_message": row[5],
            }
            for row in rows
        ]
    finally:
        await db.close()
