from datetime import datetime
from typing import Dict, List

from dashboard.src.prints.receipts.section import Section


class ReceiptFormatter:
    def __init__(self, dt: datetime = None):
        self.dt = dt or datetime.now()
        self.sections: List[Section] = []

    def add_section(self, section: Section) -> None:
        self.sections.append(section)

    def build(self) -> Dict:
        # format like "__Oct 2, 2025__"
        task_print = {
            "title": f"  {self.dt.strftime('%b')} {self.dt.day}, {self.dt.year}  ",
        }

        for section in self.sections:
            task_print[section.title] = section.render()

        return task_print
