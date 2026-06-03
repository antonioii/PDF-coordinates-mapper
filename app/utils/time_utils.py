from __future__ import annotations

from datetime import datetime


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def timestamp_for_filename() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")
