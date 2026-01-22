import json
from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass
class CalendarEvent:
    uid: str
    calendar: str
    summary: str
    recurring: bool
    start_time: str
    end_time: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
