"""データベース管理モジュール（SQLite）"""

import aiosqlite
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "river_project.db")


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    """データベースの初期化（テーブル作成）"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                source_url TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                published_date TEXT,
                collected_date TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                category TEXT,
                region TEXT
            );

            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                keyword TEXT NOT NULL,
                keyword_category TEXT,
                frequency INTEGER DEFAULT 1,
                FOREIGN KEY (article_id) REFERENCES articles(id)
            );

            CREATE TABLE IF NOT EXISTS trend_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date TEXT NOT NULL,
                keyword TEXT NOT NULL,
                keyword_category TEXT,
                count INTEGER NOT NULL,
                period TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS procurement_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                estimated_amount INTEGER,
                contract_amount INTEGER,
                business_type TEXT,
                procurement_method TEXT,
                kadou_category TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id)
            );

            CREATE TABLE IF NOT EXISTS collection_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                articles_collected INTEGER DEFAULT 0,
                status TEXT DEFAULT 'running',
                error_message TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
            CREATE INDEX IF NOT EXISTS idx_articles_collected_date ON articles(collected_date);
            CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category);
            CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword);
            CREATE INDEX IF NOT EXISTS idx_keywords_category ON keywords(keyword_category);
            CREATE INDEX IF NOT EXISTS idx_trend_snapshots_date ON trend_snapshots(snapshot_date);
            CREATE INDEX IF NOT EXISTS idx_procurement_article ON procurement_details(article_id);
            CREATE INDEX IF NOT EXISTS idx_procurement_kadou ON procurement_details(kadou_category);
        """)
        await db.commit()
