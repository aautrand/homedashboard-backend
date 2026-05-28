from datetime import datetime
from unittest.mock import patch

from dashboard.src.prints.receipts.formatter import (
    MathPrinterFormatter,
    PrinterFormatter,
    ReceiptFormatter,
)
from dashboard.src.prints.receipts.section import (
    MultiElementSection,
    SingleElementSection,
)


class TestReceiptFormatter:

    def test_build_default_title(self):
        dt = datetime(2025, 10, 2)
        rf = ReceiptFormatter(dt=dt)
        result = rf.build()
        assert result["title"] == "  Oct 2, 2025  "

    def test_build_custom_title(self):
        rf = ReceiptFormatter()
        result = rf.build(title="Custom Title")
        assert result["title"] == "Custom Title"

    def test_build_empty_title(self):
        rf = ReceiptFormatter()
        result = rf.build(title="")
        assert result["title"] == ""

    def test_add_section(self):
        rf = ReceiptFormatter()
        section = MultiElementSection(title="Weather", items=["Sunny", "Warm"])
        rf.add_section(section)
        result = rf.build()
        assert "Weather" in result
        assert result["Weather"] == ["Sunny", "Warm"]

    def test_multiple_sections(self):
        rf = ReceiptFormatter()
        rf.add_section(MultiElementSection(title="A", items=["1"]))
        rf.add_section(MultiElementSection(title="B", items=["2"]))
        result = rf.build()
        assert result["A"] == ["1"]
        assert result["B"] == ["2"]

    def test_single_element_section(self):
        rf = ReceiptFormatter()
        rf.add_section(SingleElementSection(title="Note", item="Remember"))
        result = rf.build()
        assert result["Note"] == ["Remember"]


class TestPrinterFormatter:

    def test_init(self):
        pf = PrinterFormatter()
        assert pf.instructions == {"instructions": []}

    def test_process_text(self):
        pf = PrinterFormatter()
        pf._process_text("hello")
        assert pf.instructions["instructions"] == [{"text": "hello"}]

    def test_process_textln_short(self):
        pf = PrinterFormatter()
        pf._process_textln("short line")
        assert pf.instructions["instructions"] == [{"textln": "short line"}]

    def test_process_textln_wraps_long(self):
        pf = PrinterFormatter()
        long_text = "word " * 20  # ~100 chars
        pf._process_textln(long_text.strip())
        assert len(pf.instructions["instructions"]) >= 2
        for instr in pf.instructions["instructions"]:
            assert "textln" in instr

    def test_process_ln(self):
        pf = PrinterFormatter()
        pf._process_ln(3)
        assert pf.instructions["instructions"] == [{"ln": 3}]

    def test_process_image(self):
        pf = PrinterFormatter()
        pf._process_image("http://img.png")
        instr = pf.instructions["instructions"][0]
        assert "image" in instr
        assert instr["image"]["img_source"] == "http://img.png"

    def test_process_qr(self):
        pf = PrinterFormatter()
        pf._process_qr("https://example.com")
        instr = pf.instructions["instructions"][0]
        assert "qr" in instr
        assert instr["qr"]["content"] == "https://example.com"

    def test_process_barcode(self):
        pf = PrinterFormatter()
        pf._process_barcode("1234567890123")
        instr = pf.instructions["instructions"][0]
        assert "barcode" in instr
        assert instr["barcode"]["code"] == "1234567890123"

    def test_process_set(self):
        pf = PrinterFormatter()
        pf._process_set(bold=True, align="center")
        instr = pf.instructions["instructions"][0]
        assert instr["set"]["bold"] is True
        assert instr["set"]["align"] == "center"

    def test_process_block_text(self):
        pf = PrinterFormatter()
        pf._process_block_text("block content", font="1", columns=20)
        instr = pf.instructions["instructions"][0]
        assert instr["block_text"] == "block content"
        assert instr["font"] == "1"
        assert instr["columns"] == 20


class TestMathPrinterFormatter:

    def test_add_title(self):
        mpf = MathPrinterFormatter()
        mpf.add_title("Algebra")
        instrs = mpf.instructions["instructions"]
        # Should be: set(invert=True), textln, set(invert=False), ln(2)
        assert len(instrs) == 4
        assert instrs[0]["set"]["invert"] is True
        assert "textln" in instrs[1]
        assert instrs[2]["set"]["invert"] is False
        assert instrs[3]["ln"] == 2

    @patch("dashboard.src.prints.receipts.formatter.get_storage_client")
    @patch("dashboard.src.prints.receipts.formatter.latex_to_png")
    def test_add_problems_text_element(self, mock_latex, mock_storage):
        mpf = MathPrinterFormatter()
        problems = [{"elements": [{"kind": "text", "content": "Solve for x"}]}]
        mpf.add_problems(problems)
        # Should have: textln(divider), textln(content), ln(2)
        instrs = mpf.instructions["instructions"]
        assert any("textln" in i and "Problem 1" in i.get("textln", "") for i in instrs)

    def test_add_score(self):
        mpf = MathPrinterFormatter()
        mpf.add_score(5)
        instrs = mpf.instructions["instructions"]
        assert instrs[0]["ln"] == 5
        assert "______ / 5" in instrs[1].get("textln", "")

    @patch.dict("os.environ", {"SELF_HOST": "10.0.0.1"})
    def test_add_problem_hash(self):
        mpf = MathPrinterFormatter()
        mpf.add_problem_hash("abc123")
        instrs = mpf.instructions["instructions"]
        assert (
            instrs[0]["qr"]["content"] == "http://10.0.0.1:8050/learning/score/abc123"
        )

    @patch("dashboard.src.prints.receipts.formatter.get_storage_client")
    @patch("dashboard.src.prints.receipts.formatter.latex_to_png")
    def test_process(self, mock_latex, mock_storage):
        mpf = MathPrinterFormatter()
        raw = {
            "topic": "Math",
            "problems": [{"elements": [{"kind": "text", "content": "2+2"}]}],
            "problem_hash": "hash123",
        }
        result = mpf.process(raw)
        assert "instructions" in result
        assert len(result["instructions"]) > 0
