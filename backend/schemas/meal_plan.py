from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
"""
Meal plan related Pydantic schemas
"""

class MealItem(BaseModel):
    name: str
    description: str
    calories: float
    protein: float
    carbs: float
    fat: float
    ingredients: List[str]
    instructions: Optional[str] = None


class Meal(BaseModel):
    name: str  # Breakfast, Lunch, Dinner, Snack
    items: List[MealItem]
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float


class MealPlanCreate(BaseModel):
    plan_type: str  # daily, weekly
    plan_date: Optional[datetime] = None
    preferences: Optional[Dict[str, Any]] = None


class MealPlanResponse(BaseModel):
    id: int
    user_id: int
    plan_type: str
    plan_date: datetime
    meals: Dict[str, Any]  # JSON structure with meal details
    total_calories: Optional[float] = None
    total_protein: Optional[float] = None
    total_carbs: Optional[float] = None
    total_fat: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True