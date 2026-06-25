from sqlalchemy.orm import Session

from dashboard.src.data.models.device_event import DeviceEvent


class DataManager:
    def __init__(self, db: Session):
        self.db = db

    def record_event(self, device_id: str) -> DeviceEvent:
        event = DeviceEvent(device_id=device_id)
        self.db.add(event)
        self.db.flush()
        return event
