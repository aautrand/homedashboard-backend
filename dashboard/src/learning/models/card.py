from datetime import datetime


class Card:
    def __init__(self, title, content):
        self.created_date = datetime.now()
        self.title = title
        self.content = content
        self.reviewed = False
        self.reviewed_date = None
