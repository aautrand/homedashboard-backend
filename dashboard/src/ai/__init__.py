from flask import Blueprint, Flask

ai = Blueprint("ai", __name__, url_prefix="/ai")


@ai.route("/card", methods=["POST"])
def add_card():
    print("here")
    return "something"
