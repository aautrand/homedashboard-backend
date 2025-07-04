from flask import Flask, Blueprint

ai = Blueprint("ai", __name__, url_prefix="/ai")

@ai.route('/card', methods=['POST'])
def add_card():
    print("here")
    return "something"