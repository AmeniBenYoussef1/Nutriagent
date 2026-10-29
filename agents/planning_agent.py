from dataclasses import dataclass

from items import NutritionEstimate, UserGoals
from agents import frontier_agent


@dataclass
class MacroGap:
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float

    @property
    def is_over_calories(self) -> bool:
        return self.calories < 0


def compute_gap(todays_totals: NutritionEstimate, goals: UserGoals) -> MacroGap:
    return MacroGap(
        calories=round(goals.daily_calories - todays_totals.calories, 1),
        protein_g=round(goals.protein_g - todays_totals.protein_g, 1),
        carbs_g=round(goals.carbs_g - todays_totals.carbs_g, 1),
        fat_g=round(goals.fat_g - todays_totals.fat_g, 1),
    )


def plan_next_meal(todays_totals: NutritionEstimate, goals: UserGoals) -> dict:
    gap = compute_gap(todays_totals, goals)

    remaining = NutritionEstimate(
        calories=max(gap.calories, 0),
        protein_g=max(gap.protein_g, 0),
        carbs_g=max(gap.carbs_g, 0),
        fat_g=max(gap.fat_g, 0),
        source="remaining_budget",
    )
    suggestions = frontier_agent.suggest_recipes(remaining)

    notes = []
    if gap.is_over_calories:
        notes.append(
            f"You're {abs(gap.calories):.0f} kcal over your goal today — "
            "consider a lighter next meal or more activity."
        )
    if gap.protein_g > 20:
        notes.append(f"You're {gap.protein_g:.0f}g short on protein today.")
    if not notes:
        notes.append("You're on track today — nice work.")

    return {
        "gap": gap,
        "notes": notes,
        "suggestions": suggestions,
    }
