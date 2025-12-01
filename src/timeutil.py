try:
    from datetime import UTC  # Python 3.11+
except ImportError:  # Python <3.11
    from datetime import timezone as _tz  # type: ignore
    UTC = _tz.utc  # type: ignore

