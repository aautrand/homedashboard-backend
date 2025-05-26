import json
from dataclasses import dataclass, asdict
from typing import Optional, Any, Dict, Callable


@dataclass
class Observation:
    station_id: Optional[str]
    wind_speed: Optional[float]
    wind_direction: Optional[float]
    temperature: Optional[float]
    dewpoint: Optional[float]
    visibility: Optional[float]
    raw_message: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Return a dict representation of the Observation."""
        return asdict(self)

    def to_json(self) -> str:
        """Return a JSON string representation of the Observation."""
        return json.dumps(self.to_dict())
