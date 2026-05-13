def format_duration(seconds: float) -> str:
    """Formats seconds into h m s string."""
    total = int(seconds + 0.5)
    m, s = divmod(total, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    if m:
        return f"{m}m {s:02d}s"
    return f"{s}s"