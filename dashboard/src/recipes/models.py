"""Recipe data as the dashboard uses it, independent of Tandoor's API shape."""

from dataclasses import asdict, dataclass, field
from fractions import Fraction
from typing import Optional


@dataclass(frozen=True)
class Ingredient:
    food: str
    amount: float = 0
    unit: Optional[str] = None
    note: Optional[str] = None
    # Tandoor lets a recipe group ingredients under headers ("For the sauce");
    # a header row carries its title in `food` and has no amount.
    is_header: bool = False
    no_amount: bool = False

    def display(self) -> str:
        """One readable line, e.g. "2 cups flour, sifted"."""
        if self.is_header:
            return self.food
        parts = []
        if not self.no_amount and self.amount:
            parts.append(_format_amount(self.amount))
            if self.unit:
                parts.append(self.unit)
        parts.append(self.food)
        # Tandoor's ingredient parser often leaves the comma that separated
        # food from note on the food ("garlic," + "minced").
        line = " ".join(parts).rstrip(" ,")
        return f"{line}, {self.note}" if self.note else line


@dataclass(frozen=True)
class Step:
    instruction: str
    name: str = ""
    ingredients: list[Ingredient] = field(default_factory=list)


@dataclass(frozen=True)
class RecipeSummary:
    id: int
    name: str
    description: Optional[str] = None
    servings: int = 0
    servings_text: str = ""
    working_time: int = 0
    waiting_time: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Recipe:
    id: int
    name: str
    description: Optional[str] = None
    servings: int = 0
    servings_text: str = ""
    working_time: int = 0
    waiting_time: int = 0
    source_url: Optional[str] = None
    steps: list[Step] = field(default_factory=list)

    @property
    def ingredients(self) -> list[Ingredient]:
        """Every ingredient across all steps, in recipe order."""
        return [ingredient for step in self.steps for ingredient in step.ingredients]

    def to_dict(self) -> dict:
        return asdict(self) | {
            "ingredients": [ingredient.display() for ingredient in self.ingredients]
        }


def _format_amount(amount: float) -> str:
    """Kitchen-style amounts: 2.0 -> "2", 1.5 -> "1 1/2", 0.33 -> "1/3".

    Tandoor stores amounts as decimals (a third is 0.33), so anything within
    a rounding error of a kitchen fraction (halves, thirds, quarters,
    eighths) is shown as that fraction; other values stay decimal.
    """
    if amount == int(amount):
        return str(int(amount))

    for denominator in KITCHEN_DENOMINATORS:
        fraction = Fraction(round(amount * denominator), denominator)
        if abs(float(fraction) - amount) <= 0.02:
            whole, remainder = divmod(fraction.numerator, fraction.denominator)
            if not remainder:
                return str(whole)
            part = f"{remainder}/{fraction.denominator}"
            return f"{whole} {part}" if whole else part

    return f"{amount:g}"


KITCHEN_DENOMINATORS = (2, 3, 4, 8)
