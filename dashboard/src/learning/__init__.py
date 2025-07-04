from flask import Blueprint, request

learning = Blueprint("learning", __name__, url_prefix="learning")


@learning.route("/card", methods=["POST"])
def insert_card():
    print("asdlfkjahlsdkfjhasdlk")
