"""
Timezone utilities for BayScan.

Ensures all times displayed to users are in Central Standard Time (America/Chicago).
All internal storage remains in UTC.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

# Central timezone
CENTRAL_TZ = ZoneInfo("America/Chicago")
UTC_TZ = ZoneInfo("UTC")


def utc_to_central(utc_dt: datetime) -> datetime:
    """
    Convert UTC datetime to Central time.

    Args:
        utc_dt: Naive or UTC datetime object

    Returns:
        Datetime in Central timezone (America/Chicago)
    """
    if utc_dt is None:
        return None

    # If naive, assume UTC
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=UTC_TZ)

    # Convert to Central
    return utc_dt.astimezone(CENTRAL_TZ)


def format_central_time(utc_dt: datetime, include_timezone: bool = True) -> str:
    """
    Format UTC datetime as Central time string.

    Args:
        utc_dt: UTC datetime object
        include_timezone: Whether to append " CST" or " CDT" to the string

    Returns:
        Formatted string like "3:45 PM CST" or "3:45 PM"
    """
    if utc_dt is None:
        return ""

    central_dt = utc_to_central(utc_dt)
    time_str = central_dt.strftime("%I:%M %p").lstrip("0")  # Remove leading zero from hour

    if include_timezone:
        # Get timezone abbreviation (CST or CDT)
        tz_abbr = central_dt.strftime("%Z")
        return f"{time_str} {tz_abbr}"

    return time_str


def format_central_datetime(utc_dt: datetime, include_timezone: bool = True) -> str:
    """
    Format UTC datetime as Central date and time string.

    Args:
        utc_dt: UTC datetime object
        include_timezone: Whether to append timezone abbreviation

    Returns:
        Formatted string like "Nov 23, 3:45 PM CST"
    """
    if utc_dt is None:
        return ""

    central_dt = utc_to_central(utc_dt)
    date_str = central_dt.strftime("%b %d")
    time_str = central_dt.strftime("%I:%M %p").lstrip("0")

    if include_timezone:
        tz_abbr = central_dt.strftime("%Z")
        return f"{date_str}, {time_str} {tz_abbr}"

    return f"{date_str}, {time_str}"


def get_central_isoformat(utc_dt: datetime) -> str:
    """
    Convert UTC datetime to ISO format string with Central timezone.

    Args:
        utc_dt: UTC datetime object

    Returns:
        ISO format string with timezone offset (e.g., "2024-11-23T14:30:00-06:00")
    """
    if utc_dt is None:
        return ""

    central_dt = utc_to_central(utc_dt)
    return central_dt.isoformat()


def central_now() -> datetime:
    """
    Get current datetime in Central timezone.

    Returns:
        Current datetime in America/Chicago timezone
    """
    return datetime.now(CENTRAL_TZ)


def central_to_utc(central_dt: datetime) -> datetime:
    """
    Convert Central datetime to UTC for database storage.

    Args:
        central_dt: Naive datetime representing Central time, or aware Central datetime

    Returns:
        UTC datetime (naive, for database storage)
    """
    if central_dt is None:
        return None

    # If naive, treat as Central time
    if central_dt.tzinfo is None:
        central_dt = central_dt.replace(tzinfo=CENTRAL_TZ)

    # Convert to UTC and make naive for database storage
    utc_dt = central_dt.astimezone(UTC_TZ)
    return utc_dt.replace(tzinfo=None)
