import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from items import FoodItem, UserGoals, NutritionEstimate
from agents import specialist_agent, planning_agent


def test_heuristic_estimate_known_food():
    item = FoodItem(name="grilled chicken breast", estimated_portion="150g")
    est = specialist_agent.estimate(item)
    assert est.calories > 0
    assert est.source == "heuristic"


def test_heuristic_estimate_unknown_food():
    item = FoodItem(name="mystery casserole", estimated_portion="1 serving")
    est = specialist_agent.estimate(item)
    assert est.calories > 0  # generic fallback, never zero


def test_meal_totals_sum_items():
    items = [
        FoodItem(name="egg", estimated_portion="2 piece"),
        FoodItem(name="bread", estimated_portion="1 slice"),
    ]
    total = specialist_agent.estimate_meal(items)
    individual_sum = sum(specialist_agent.estimate(i).calories for i in items)
    assert abs(total.calories - individual_sum) < 0.01


def test_compute_gap_under_goal():
    totals = NutritionEstimate(1000, 50, 100, 30)
    goals = UserGoals(daily_calories=2000, protein_g=120, carbs_g=220, fat_g=65)
    gap = planning_agent.compute_gap(totals, goals)
    assert gap.calories == 1000
    assert gap.protein_g == 70
    assert not gap.is_over_calories


def test_compute_gap_over_goal():
    totals = NutritionEstimate(2500, 150, 250, 90)
    goals = UserGoals(daily_calories=2000, protein_g=120, carbs_g=220, fat_g=65)
    gap = planning_agent.compute_gap(totals, goals)
    assert gap.is_over_calories


if __name__ == "__main__":
    test_heuristic_estimate_known_food()
    test_heuristic_estimate_unknown_food()
    test_meal_totals_sum_items()
    test_compute_gap_under_goal()
    test_compute_gap_over_goal()
    print("All tests passed.")
