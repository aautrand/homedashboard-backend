from typing import Dict, Any


def _get(d: Dict, *keys) -> Any:
    for k in keys:
        d = d.get(k, {})
    return d.get("value") if isinstance(d, dict) else None