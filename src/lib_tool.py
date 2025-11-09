from typing import Any

def print_major_error(title:str, msg:str)->None:
    print(f"[{title}] {msg}")

def find_dict(data: list[dict[str, Any]], key: str, value: Any) -> dict[str, Any] | None:
    """Return the first dict in `data` where dict[key] == value."""
    return next((d for d in data if d.get(key) == value), None)