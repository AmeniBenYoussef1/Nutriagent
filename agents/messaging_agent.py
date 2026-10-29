from items import NutritionEstimate, UserGoals
from agents.planning_agent import plan_next_meal


def build_digest_text(todays_totals: NutritionEstimate, goals: UserGoals) -> str:
    plan = plan_next_meal(todays_totals, goals)
    gap = plan["gap"]

    lines = [
        " Daily Nutrition Digest",
        "",
        f"Calories: {todays_totals.calories:.0f} / {goals.daily_calories:.0f} kcal",
        f"Protein:  {todays_totals.protein_g:.0f}g / {goals.protein_g:.0f}g",
        f"Carbs:    {todays_totals.carbs_g:.0f}g / {goals.carbs_g:.0f}g",
        f"Fat:      {todays_totals.fat_g:.0f}g / {goals.fat_g:.0f}g",
        "",
    ]
    lines.extend(plan["notes"])

    if plan["suggestions"]:
        lines.append("")
        lines.append("Suggested next meal:")
        top = plan["suggestions"][0]
        lines.append(f"  → {top.get('recipe', 'Recipe')}")

    return "\n".join(lines)


def send_digest(todays_totals: NutritionEstimate, goals: UserGoals) -> str:
    text = build_digest_text(todays_totals, goals)
    # TODO: integrate real notifications, e.g.:
    # requests.post("https://api.pushover.net/1/messages.json", data={...})
    return text
