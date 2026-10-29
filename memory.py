import json
import os
from datetime import datetime, date
from typing import Optional

from items import LoggedMeal, FoodItem, NutritionEstimate, UserGoals
import config


class Memory:
    def __init__(self, path: str = config.MEMORY_PATH):
        self.path = path
        self._data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                return json.load(f)
        return {"meals": [], "goals": UserGoals().to_dict()}

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=2, default=str)

    # ---- meals ----

    def add_meal(self, meal: LoggedMeal):
        self._data["meals"].append(meal.to_dict())
        self._save()

    def meals_for_date(self, day: Optional[date] = None) -> list[dict]:
        day = day or date.today()
        return [
            m
            for m in self._data["meals"]
            if datetime.fromisoformat(m["timestamp"]).date() == day
        ]

    def todays_totals(self) -> NutritionEstimate:
        totals = NutritionEstimate(0, 0, 0, 0, source="daily_total")
        for m in self.meals_for_date():
            est = m.get("estimate")
            if est:
                totals = totals + NutritionEstimate(
                    calories=est["calories"],
                    protein_g=est["protein_g"],
                    carbs_g=est["carbs_g"],
                    fat_g=est["fat_g"],
                )
        return totals

    def history(self, n_days: int = 14) -> list[dict]:
        """Return per-day totals for the last n_days, for the trend chart."""
        by_day: dict[str, NutritionEstimate] = {}
        for m in self._data["meals"]:
            d = datetime.fromisoformat(m["timestamp"]).date().isoformat()
            est = m.get("estimate")
            if not est:
                continue
            running = by_day.get(d, NutritionEstimate(0, 0, 0, 0))
            by_day[d] = running + NutritionEstimate(
                calories=est["calories"],
                protein_g=est["protein_g"],
                carbs_g=est["carbs_g"],
                fat_g=est["fat_g"],
            )
        days = sorted(by_day.keys())[-n_days:]
        return [{"date": d, **by_day[d].to_dict()} for d in days]

    # ---- goals ----

    def get_goals(self) -> UserGoals:
        return UserGoals(**self._data["goals"])

    def set_goals(self, goals: UserGoals):
        self._data["goals"] = goals.to_dict()
        self._save()
