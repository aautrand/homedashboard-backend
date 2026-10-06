from dashboard.src.recipes.models import Ingredient, Recipe, Step


class TestIngredientDisplay:
    def test_amount_unit_food_note(self):
        ingredient = Ingredient(food="flour", amount=2.0, unit="cups", note="sifted")

        assert ingredient.display() == "2 cups flour, sifted"

    def test_fractional_amount_without_unit(self):
        assert Ingredient(food="lemon", amount=0.5).display() == "1/2 lemon"

    def test_amounts_read_as_kitchen_fractions(self):
        def shown(amount):
            return Ingredient(food="x", amount=amount, unit="cup").display()

        assert shown(0.33) == "1/3 cup x"
        assert shown(0.25) == "1/4 cup x"
        assert shown(1.5) == "1 1/2 cup x"
        assert shown(2.0) == "2 cup x"

    def test_odd_amount_stays_decimal(self):
        assert Ingredient(food="x", amount=0.437, unit="g").display() == "0.437 g x"

    def test_trailing_comma_on_food_is_not_doubled(self):
        ingredient = Ingredient(food="garlic,", amount=4, unit="cloves", note="minced")

        assert ingredient.display() == "4 cloves garlic, minced"

    def test_no_amount(self):
        ingredient = Ingredient(food="salt", amount=0, no_amount=True)

        assert ingredient.display() == "salt"

    def test_header(self):
        assert Ingredient(food="For the sauce", is_header=True).display() == (
            "For the sauce"
        )


class TestRecipe:
    def test_ingredients_flatten_steps_in_order(self):
        recipe = Recipe(
            id=1,
            name="Pancakes",
            steps=[
                Step(instruction="Mix", ingredients=[Ingredient(food="flour")]),
                Step(instruction="Fry", ingredients=[Ingredient(food="butter")]),
            ],
        )

        assert [i.food for i in recipe.ingredients] == ["flour", "butter"]

    def test_to_dict_includes_readable_ingredients(self):
        recipe = Recipe(
            id=1,
            name="Toast",
            steps=[
                Step(
                    instruction="Toast it",
                    ingredients=[Ingredient(food="bread", amount=2, unit="slices")],
                )
            ],
        )

        data = recipe.to_dict()

        assert data["name"] == "Toast"
        assert data["ingredients"] == ["2 slices bread"]
        assert data["steps"][0]["instruction"] == "Toast it"
