"""
Utility helpers — common functions used across the backend.
"""

from datetime import datetime, timedelta
from typing import Optional


def format_timestamp(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO 8601 string for API responses."""
    if dt is None:
        return None
    return dt.isoformat() + "Z"


def parse_timestamp(ts_string: str) -> datetime:
    """Parse an ISO 8601 timestamp string to datetime."""
    # Handle various ISO formats
    for fmt in [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ]:
        try:
            return datetime.strptime(ts_string, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unable to parse timestamp: {ts_string}")


def get_time_ago(dt: datetime) -> str:
    """
    Convert a datetime to a human-readable 'time ago' string.
    e.g., "5 minutes ago", "2 hours ago", "1 day ago"
    """
    now = datetime.utcnow()
    diff = now - dt

    seconds = int(diff.total_seconds())

    if seconds < 60:
        return f"{seconds} seconds ago"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    else:
        days = seconds // 86400
        return f"{days} day{'s' if days > 1 else ''} ago"


def paginate_list(items: list, page: int, page_size: int) -> dict:
    """
    Simple list pagination helper.

    Returns:
        dict with keys: data, total, page, page_size
    """
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "data": items[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
