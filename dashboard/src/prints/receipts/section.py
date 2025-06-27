from abc import ABC, abstractmethod
from typing import Any, Callable, List


class Section(ABC):
    def __init__(self, title: str, bullet: str = ""):
        self.title = title
        self.bullet = bullet

    @abstractmethod
    def _content_lines(self) -> List[str]: ...

    def render(self) -> List[str]:
        lines = [f"_{self.title}_"]
        lines.extend(self._content_lines())
        return lines


class MultiElementSection(Section):
    def __init__(
        self,
        title: str,
        items: List[Any],
        bullet: str = "",
        formatter: Callable[[Any], str] = lambda x: str(x),
    ):
        super().__init__(title, bullet)
        self.items = items
        self.formatter = formatter

    def _content_lines(self) -> List[str]:
        return [self.bullet + self.formatter(itm) for itm in self.items]


class SingleElementSection(Section):
    def __init__(self, title: str, item: str, bullet: str = ""):
        super().__init__(title, bullet)
        self.item = item

    def _content_lines(self) -> List[str]:
        return [self.bullet + self.item]
