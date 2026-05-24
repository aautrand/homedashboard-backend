import pytest

from dashboard.src.prints.receipts.section import (MultiElementSection,
                                                   Section,
                                                   SingleElementSection)


class TestSectionABC:

    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            Section("Title")


class TestMultiElementSection:

    def test_render_basic(self):
        section = MultiElementSection(title="Items", items=["a", "b", "c"])
        lines = section.render()
        assert lines == ["a", "b", "c"]

    def test_render_with_bullet(self):
        section = MultiElementSection(title="Items", items=["a", "b"], bullet="- ")
        lines = section.render()
        assert lines == ["- a", "- b"]

    def test_render_with_formatter(self):
        section = MultiElementSection(
            title="Events",
            items=[("10:00", "Meeting"), ("14:00", "Lunch")],
            formatter=lambda t: f"{t[0]} - {t[1]}",
        )
        lines = section.render()
        assert lines == ["10:00 - Meeting", "14:00 - Lunch"]

    def test_render_with_bullet_and_formatter(self):
        section = MultiElementSection(
            title="Events",
            items=[("10:00", "Meeting")],
            bullet="* ",
            formatter=lambda t: f"{t[0]} - {t[1]}",
        )
        lines = section.render()
        assert lines == ["* 10:00 - Meeting"]

    def test_empty_items(self):
        section = MultiElementSection(title="Empty", items=[])
        assert section.render() == []

    def test_title_and_bullet_stored(self):
        section = MultiElementSection(title="T", items=[], bullet=">>")
        assert section.title == "T"
        assert section.bullet == ">>"


class TestSingleElementSection:

    def test_render(self):
        section = SingleElementSection(title="Note", item="Hello world")
        assert section.render() == ["Hello world"]

    def test_render_with_bullet(self):
        section = SingleElementSection(title="Note", item="Hello", bullet="* ")
        assert section.render() == ["* Hello"]

    def test_title_stored(self):
        section = SingleElementSection(title="T", item="x")
        assert section.title == "T"
