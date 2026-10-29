"""Core data classes shared across all agents."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class FoodItem:

    name: str
    estimated_portion: str  
    confidence: float = 0.7 

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class NutritionEstimate:

    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    source: str = "unknown"  

    def __add__(self, other: "NutritionEstimate") -> "NutritionEstimate":
        return NutritionEstimate(
            calories=self.calories + other.calories,
            protein_g=self.protein_g + other.protein_g,
            carbs_g=self.carbs_g + other.carbs_g,
            fat_g=self.fat_g + other.fat_g,
            source="combined",
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LoggedMeal:

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    items: list[FoodItem] = field(default_factory=list)
    estimate: Optional[NutritionEstimate] = None
    label: str = ""  

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


@dataclass
class UserGoals:

    daily_calories: float = 2000
    protein_g: float = 120
    carbs_g: float = 220
    fat_g: float = 65
    goal_type: str = "maintain"  

    def to_dict(self) -> dict:
        return asdict(self)
