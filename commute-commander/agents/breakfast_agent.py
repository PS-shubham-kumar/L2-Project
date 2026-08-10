from __future__ import annotations

import re
from mcp_tools.recipe_tools import RecipeTool


def _parse_minutes(time_val) -> int:
    """Extract an integer minute count from various formats ('10', '10 min', '15 minutes')."""
    if isinstance(time_val, int):
        return time_val
    m = re.search(r"(\d+)", str(time_val))
    return int(m.group(1)) if m else 10


def _make_steps(recipe_name: str, ingredients: list) -> list[str]:
    """Generate plausible steps when the API doesn't return them."""
    ing_list = ", ".join(ingredients) if ingredients else "your ingredients"
    return [
        f"Gather your ingredients: {ing_list}.",
        f"Prep and measure everything before you start.",
        f"Cook the {recipe_name} over medium heat, stirring occasionally.",
        "Plate and serve immediately.",
    ]


class BreakfastAgent:
    def __init__(self) -> None:
        self.tool = RecipeTool()

    def run(self, ingredients: list, time_constraint: str) -> str:
        recipe = self.tool.get_recipe(ingredients, time_constraint)
        return f"## Breakfast\n- {recipe['name']}\n- Time: {recipe['time']}\n- Ingredients: {', '.join(recipe['ingredients'])}"

    def run_structured(self, ingredients: list, time_constraint) -> dict:
        """Return typed dict matching the API contract §3.4 shape."""
        recipe: dict = self.tool.get_recipe(ingredients, time_constraint)
        name: str = recipe.get("name", "Quick breakfast")
        used: list = recipe.get("ingredients", ingredients or ["eggs"])
        prep: int = _parse_minutes(recipe.get("time", time_constraint))

        steps: list = recipe.get("steps") or _make_steps(name, used)

        # Fetch one alternate suggestion with a different primary ingredient
        alt_ingredients = ["oats"] if "egg" in " ".join(used).lower() else ["eggs"]
        try:
            alt = self.tool.get_recipe(alt_ingredients, time_constraint)
            alternates = [
                {
                    "recipe_name": alt.get("name", "Oat bowl"),
                    "prep_time_minutes": _parse_minutes(alt.get("time", time_constraint)),
                }
            ]
        except Exception:
            alternates = [{"recipe_name": "Oat bowl", "prep_time_minutes": prep}]

        return {
            "section": "breakfast",
            "status": "success",
            "data": {
                "recipe_name": name,
                "prep_time_minutes": prep,
                "ingredients_used": used,
                "steps": steps,
                "alternates": alternates,
            },
        }
