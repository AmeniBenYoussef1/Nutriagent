from items import FoodItem, NutritionEstimate
from agents import specialist_agent, frontier_agent

SPECIALIST_WEIGHT = 0.65


def estimate_item(item: FoodItem) -> NutritionEstimate:
    specialist_est = specialist_agent.estimate(item)
    frontier_est = frontier_agent.estimate(item)

    if frontier_est.source in ("frontier_unavailable", "frontier_no_match"):
        return specialist_est  

    w = SPECIALIST_WEIGHT
    return NutritionEstimate(
        calories=round(w * specialist_est.calories + (1 - w) * frontier_est.calories, 1),
        protein_g=round(w * specialist_est.protein_g + (1 - w) * frontier_est.protein_g, 1),
        carbs_g=round(w * specialist_est.carbs_g + (1 - w) * frontier_est.carbs_g, 1),
        fat_g=round(w * specialist_est.fat_g + (1 - w) * frontier_est.fat_g, 1),
        source="ensemble",
    )


def estimate_meal(items: list[FoodItem]) -> NutritionEstimate:
    total = NutritionEstimate(0, 0, 0, 0, source="ensemble")
    for item in items:
        total = total + estimate_item(item)
    return total
