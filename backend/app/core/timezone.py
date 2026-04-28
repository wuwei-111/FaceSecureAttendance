from datetime import datetime, timezone
from zoneinfo import ZoneInfo


BEIJING_TZ = ZoneInfo("Asia/Shanghai")


def to_beijing_time(dt: datetime | None) -> datetime:
    if dt is None:
        return datetime.now(BEIJING_TZ)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc).astimezone(BEIJING_TZ)
    return dt.astimezone(BEIJING_TZ)
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


BEIJING_TZ = ZoneInfo("Asia/Shanghai")


def to_beijing_time(dt: datetime | None) -> datetime:
    if dt is None:
        return datetime.now(BEIJING_TZ)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc).astimezone(BEIJING_TZ)
    return dt.astimezone(BEIJING_TZ)
