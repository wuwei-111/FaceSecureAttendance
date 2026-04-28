"""SQLite 轻量迁移：为已有 attendance.db 追加缺失列。"""

from sqlalchemy import inspect, text

from app.core.database import engine


def ensure_sqlite_columns() -> None:
    if engine.url.drivername != "sqlite":
        return

    insp = inspect(engine)

    try:
        cols_gp = [c["name"] for c in insp.get_columns("group_photos")]
    except Exception:
        return

    with engine.begin() as conn:
        if "detail_json" not in cols_gp:
            conn.execute(text("ALTER TABLE group_photos ADD COLUMN detail_json TEXT"))
