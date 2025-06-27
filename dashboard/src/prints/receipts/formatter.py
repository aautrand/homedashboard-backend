from datetime import datetime
from typing import List

from dashboard.src.prints.receipts.section import Section


class ReceiptFormatter:
    def __init__(self, dt: datetime = None):
        self.dt = dt or datetime.now()
        self.sections: List[Section] = []

    def add_section(self, section: Section) -> None:
        self.sections.append(section)

    def build(self) -> bytes:
        # format like "__Oct 2, 2025__"
        header = f"__{self.dt.strftime('%b')} {self.dt.day}, {self.dt.year}__"
        all_lines = [header, ""]
        for sec in self.sections:
            all_lines.extend(sec.render())
            all_lines.append("")
        if all_lines and all_lines[-1] == "":
            all_lines.pop()
        final_text = "\r\n".join(all_lines) + "\r\n"
        return final_text.encode("utf-8")
