import requests

from mcp_tools.framework_mcp import MCPToolRegistry

registry = MCPToolRegistry()


@registry.tool(name="get_recipe", description="Suggest a quick recipe based on available ingredients and time")
def get_recipe(ingredients: list, time_constraint: str) -> dict:
    if not ingredients:
        ingredients = ["egg"]
    ingredient_query = ",".join(ingredients)
    try:
        response = requests.get("https://www.themealdb.com/api/json/v1/1/filter.php", params={"i": ingredient_query}, timeout=10)
        response.raise_for_status()
        meals = response.json().get("meals") or []
        if meals:
            meal = meals[0]
            return {
                "name": meal.get("strMeal", "Quick egg meal"),
                "time": time_constraint,
                "ingredients": ingredients,
            }
    except Exception:
        pass
    return {
        "name": "Quick scrambled eggs",
        "time": time_constraint,
        "ingredients": ingredients,
    }


class RecipeTool:
    def get_recipe(self, ingredients: list, time_constraint: str) -> dict:
        return registry.call("get_recipe", ingredients, time_constraint)
