def escape_like(s: str) -> str:
    return s.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
