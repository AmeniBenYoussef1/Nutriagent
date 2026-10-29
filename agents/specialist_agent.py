import re
import requests

from items import FoodItem, NutritionEstimate
import config


_HEURISTIC_TABLE = {
    "chicken": (165, 31, 0, 3.6),
    "rice": (130, 2.7, 28, 0.3),
    "broccoli": (34, 2.8, 7, 0.4),
    "egg": (155, 13, 1.1, 11),
    "bread": (265, 9, 49, 3.2),
    "milk": (61, 3.2, 4.8, 3.3),
    "cheese": (402, 25, 1.3, 33),
    "apple": (52, 0.3, 14, 0.2),
    "banana": (89, 1.1, 23, 0.3),
    "salmon": (208, 20, 0, 13),
    "pasta": (131, 5, 25, 1.1),
    "beef": (250, 26, 0, 17),
    "avocado": (160, 2, 9, 15),
    "yogurt": (59, 10, 3.6, 0.4),
    "beans": (127, 9, 23, 0.5),
}

_PORTION_GRAMS = {
    "cup": 200,
    "slice": 30,
    "tbsp": 15,
    "tsp": 5,
    "serving": 150,
    "piece": 100,
}


def _portion_to_grams(portion: str) -> float:
    match = re.search(r"([\d.]+)\s*g\b", portion)
    if match:
        return float(match.group(1))
    match = re.search(r"([\d.]+)", portion)
    quantity = float(match.group(1)) if match else 1.0
    for unit, grams in _PORTION_GRAMS.items():
        if unit in portion.lower():
            return quantity * grams
    return quantity * 100  # default assumption: ~100g per unit


def _heuristic_estimate(item: FoodItem) -> NutritionEstimate:
    grams = _portion_to_grams(item.estimated_portion)
    name_lower = item.name.lower()
    match = next((k for k in _HEURISTIC_TABLE if k in name_lower), None)
    if match is None:
        cal, protein, carbs, fat = (150, 5, 20, 5)
    else:
        cal, protein, carbs, fat = _HEURISTIC_TABLE[match]
    scale = grams / 100
    return NutritionEstimate(
        calories=round(cal * scale, 1),
        protein_g=round(protein * scale, 1),
        carbs_g=round(carbs * scale, 1),
        fat_g=round(fat * scale, 1),
        source="heuristic",
    )


def _modal_estimate(item: FoodItem) -> NutritionEstimate:
    response = requests.post(
        config.MODAL_SPECIALIST_URL,
        json={"name": item.name, "portion": item.estimated_portion},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    return NutritionEstimate(
        calories=data["calories"],
        protein_g=data["protein_g"],
        carbs_g=data["carbs_g"],
        fat_g=data["fat_g"],
        source="specialist",
    )


def estimate(item: FoodItem) -> NutritionEstimate:

    if config.MODAL_SPECIALIST_URL:
        try:
            return _modal_estimate(item)
        except (requests.RequestException, KeyError):
            pass  # fall through to heuristic
    return _heuristic_estimate(item)


def estimate_meal(items: list[FoodItem]) -> NutritionEstimate:
    total = NutritionEstimate(0, 0, 0, 0, source="specialist")
    for item in items:
        total = total + estimate(item)
    return total
