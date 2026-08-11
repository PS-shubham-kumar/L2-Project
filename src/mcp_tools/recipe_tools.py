"""Recipe tool — fetches recipes from TheMealDB API including full cooking steps."""
import requests

from fastmcp import FastMCP

mcp = FastMCP("recipe-server")


def _fetch_meal_details(meal_id: str) -> dict:
    """Fetch full meal details (including instructions) from TheMealDB by ID."""
    try:
        r = requests.get(
            "https://www.themealdb.com/api/json/v1/1/lookup.php",
            params={"i": meal_id},
            timeout=10,
        )
        r.raise_for_status()
        meals = r.json().get("meals") or []
        if meals:
            return meals[0]
    except Exception:
        pass
    return {}


def _extract_ingredients_from_meal(meal: dict) -> list[str]:
    """Extract non-empty ingredient entries from a full meal record."""
    ingredients = []
    for i in range(1, 21):
        ing = (meal.get(f"strIngredient{i}") or "").strip()
        measure = (meal.get(f"strMeasure{i}") or "").strip()
        if ing:
            ingredients.append(f"{measure} {ing}".strip() if measure else ing)
    return ingredients


def _parse_instructions(instructions: str) -> list[str]:
    """Split raw instruction text into a clean list of steps."""
    if not instructions:
        return []
    import re
    # Split on numbered steps like "1. Step" or "Step 1:" or "\r\n\r\n"
    raw = re.split(r"\r?\n\r?\n|(?<=[.!?])\s+(?=[A-Z])", instructions.strip())
    steps = []
    for part in raw:
        part = part.strip()
        if part and len(part) > 5:
            # Remove leading numbering like "1. " or "Step 1: "
            part = re.sub(r"^(?:step\s*)?\d+[.):\-]\s*", "", part, flags=re.IGNORECASE)
            if part:
                steps.append(part)
    return steps[:12]  # cap at 12 steps for UI clarity


@mcp.tool(name="get_recipe", description="Suggest a quick recipe based on available ingredients and time")
def get_recipe(ingredients: list, time_constraint: str) -> dict:
    if not ingredients:
        ingredients = ["egg"]
    ingredient_query = ",".join(ingredients[:3])  # MealDB supports up to ~3 ingredients

    meal_detail: dict = {}
    try:
        # Step 1: find meals matching ingredients
        r = requests.get(
            "https://www.themealdb.com/api/json/v1/1/filter.php",
            params={"i": ingredient_query},
            timeout=10,
        )
        r.raise_for_status()
        meals = r.json().get("meals") or []
        if meals:
            meal = meals[0]
            meal_id = meal.get("idMeal", "")
            # Step 2: get full details including steps
            if meal_id:
                meal_detail = _fetch_meal_details(meal_id)
    except Exception:
        pass

    if meal_detail:
        name = meal_detail.get("strMeal", "Quick breakfast")
        raw_instructions = meal_detail.get("strInstructions", "")
        steps = _parse_instructions(raw_instructions)
        used_ingredients = _extract_ingredients_from_meal(meal_detail)
        if not used_ingredients:
            used_ingredients = ingredients
        return {
            "name": name,
            "time": time_constraint,
            "ingredients": used_ingredients,
            "steps": steps,
            "category": meal_detail.get("strCategory", ""),
            "area": meal_detail.get("strArea", ""),
            "thumbnail": meal_detail.get("strMealThumb", ""),
        }

    # Fallback
    return {
        "name": "Quick scrambled eggs",
        "time": time_constraint,
        "ingredients": ingredients,
        "steps": [
            "Crack 2–3 eggs into a bowl and whisk with a pinch of salt and pepper.",
            "Heat a non-stick pan over medium-low heat and add a knob of butter.",
            "Pour in the eggs and gently stir with a spatula as they begin to set.",
            "Remove from heat while still slightly runny — residual heat will finish them.",
            "Serve immediately on toast or with your choice of sides.",
        ],
    }


class RecipeTool:
    def get_recipe(self, ingredients: list, time_constraint: str) -> dict:
        return get_recipe(ingredients, time_constraint)


if __name__ == "__main__":
    mcp.run()
