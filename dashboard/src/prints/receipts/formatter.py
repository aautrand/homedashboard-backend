import os
import tempfile
import textwrap
from datetime import datetime
from typing import Dict, List

from dashboard.src.prints.receipts.section import Section
from dashboard.src.storage import get_storage_client
from dashboard.src.utils.helpers import get_hash, latex_to_png


class ReceiptFormatter:
    def __init__(self, dt: datetime = None):
        self.dt = dt or datetime.now()
        self.sections: List[Section] = []

    def add_section(self, section: Section) -> None:
        self.sections.append(section)

    def build(self, title=None) -> Dict:
        # format like "__Oct 2, 2025__"
        if title is None:
            task_print = {
                "title": f"  {self.dt.strftime('%b')} {self.dt.day}, {self.dt.year}  ",
            }
        else:
            task_print = {"title": title}

        for section in self.sections:
            task_print[section.title] = section.render()

        return task_print


class PrinterFormatter:

    def __init__(self):
        self.instructions = {"instructions": []}

    def _process_latex(
        self,
        img_source,
        high_density_vertical=True,
        high_density_horizontal=True,
        impl="bitImageRaster",
        fragment_height=960,
        center=False,
    ):
        latex_hash = get_hash(img_source)
        out_dir = tempfile.gettempdir()
        fname = os.path.join(out_dir, f"{latex_hash}.png")
        latex_to_png(img_source, fname, fontsize=9, dpi=300, pad_inches=0.05)

        # Upload to MinIO
        storage_client = get_storage_client("minio")
        file_location = storage_client.upload_file(fname)

        self.instructions["instructions"].append(
            {
                "image": {
                    "img_source": file_location,
                    "high_density_vertical": high_density_vertical,
                    "high_density_horizontal": high_density_horizontal,
                    "impl": impl,
                    "fragment_height": fragment_height,
                    "center": center,
                }
            }
        )

    def _process_image(
        self,
        img_source,
        high_density_vertical=True,
        high_density_horizontal=True,
        impl="bitImageRaster",
        fragment_height=960,
        center=False,
    ):
        self.instructions["instructions"].append(
            {
                "image": {
                    "img_source": img_source,
                    "high_density_vertical": high_density_vertical,
                    "high_density_horizontal": high_density_horizontal,
                    "impl": impl,
                    "fragment_height": fragment_height,
                    "center": center,
                }
            }
        )

    def _process_qr(
        self,
        content,
        ec=0,
        size=3,
        model=2,
        native=False,
        center=False,
        impl=None,
        image_arguments=None,
    ):
        self.instructions["instructions"].append(
            {
                "qr": {
                    "content": content,
                    "ec": ec,
                    "size": size,
                    "model": model,
                    "native": native,
                    "center": center,
                    "impl": impl,
                    "image_arguments": image_arguments,
                }
            }
        )

    def _process_barcode(
        self,
        code,
        bc="EAN13",
        height=64,
        width=3,
        pos="BELOW",
        font="A",
        align_ct=True,
        function_type=None,
        check=True,
        force_software=False,
    ):
        self.instructions["instructions"].append(
            {
                "barcode": {
                    "code": code,
                    "bc": bc,
                    "height": height,
                    "width": width,
                    "pos": pos,
                    "font": font,
                    "align_ct": align_ct,
                    "function_type": function_type,
                    "check": check,
                    "force_software": force_software,
                }
            }
        )

    def _process_text(self, text):
        self.instructions["instructions"].append({"text": text})

    def _process_textln(self, text):
        max_width = 42
        # wrap on word boundaries, never cutting words
        lines = textwrap.wrap(
            text, width=max_width, break_long_words=False, replace_whitespace=False
        )
        for line in lines:
            self.instructions["instructions"].append({"textln": line})

    def _process_ln(self, count=1):
        self.instructions["instructions"].append({"ln": count})

    def _process_set(
        self,
        align=None,
        font=None,
        bold=None,
        underline=None,
        width=None,
        height=None,
        density=None,
        invert=None,
        smooth=None,
        flip=None,
        normal_textsize=None,
        double_width=None,
        double_height=None,
        custom_size=None,
    ):
        self.instructions["instructions"].append(
            {
                "set": {
                    "align": align,
                    "font": font,
                    "bold": bold,
                    "underline": underline,
                    "width": width,
                    "height": height,
                    "density": density,
                    "invert": invert,
                    "smooth": smooth,
                    "flip": flip,
                    "normal_textsize": normal_textsize,
                    "double_width": double_width,
                    "double_height": double_height,
                    "custom_size": custom_size,
                },
            }
        )

    def _process_block_text(self, txt, font="0", columns=None):
        self.instructions["instructions"].append(
            {
                "block_text": txt,
                "font": font,
                "columns": columns,
            }
        )


class MathPrinterFormatter(PrinterFormatter):

    def add_title(self, title):
        self._process_set(invert=True)
        self._process_textln(title)
        self._process_set(invert=False)
        self._process_ln(2)

    def add_problems(self, problems):
        for idx, problem in enumerate(problems, start=1):

            self._process_textln(f"-----------Problem {str(idx)} ------------")
            for element in problem["elements"]:
                if element["kind"] == "text":
                    self._process_textln(element["content"])
                if element["kind"] == "latex":
                    self._process_latex(element["content"])
                if element["kind"] == "image":
                    self._process_textln(element["content"])
                if element["kind"] == "barcode":
                    self._process_barcode(element["content"])
                if element["kind"] == "qr":
                    self._process_qr(element["content"])
            self._process_ln(2)

    def add_problem_hash(self, problem_hash):
        self_host = os.getenv("SELF_HOST", "localhost")
        self._process_qr(f"http://{self_host}:8050/learning/score/{problem_hash}")

    def add_score(self, problem_count):
        self._process_ln(5)
        self._process_textln(f"______ / {problem_count}")

    def process(self, raw_problems):
        self.add_title(raw_problems["topic"])
        self.add_problems(raw_problems["problems"])
        self.add_score(len(raw_problems["problems"]))
        self.add_problem_hash(raw_problems["problem_hash"])

        return self.instructions
