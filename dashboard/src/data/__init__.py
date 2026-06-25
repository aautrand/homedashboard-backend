from logging import getLogger

from flask import Blueprint, request

from dashboard.src.data.data_manager import DataManager

logger = getLogger(__name__)

data = Blueprint("data", __name__, url_prefix="/data")


@data.route("/event", methods=["POST"])
def record_event():
    payload = request.get_json()
    device_id = payload.get("id")

    if not device_id:
        return {"error": "id is required"}, 400

    manager = DataManager(request.db)
    event = manager.record_event(device_id)
    logger.info(f"Recorded event for device {device_id!r} (event_id={event.id})")

    return {"status": "ok", "event_id": event.id}, 201
