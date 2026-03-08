from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class FoodItem(BaseModel):
    name: str
    quantity: float
    unit: str
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None


class FoodAnalysisRequest(BaseModel):
    food_input: str
    serving_size: Optional[str] = None


class FoodAnalysisResponse(BaseModel):
    id: int
    user_id: int
    food_input: str
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None
    sugar: Optional[float] = None
    sodium: Optional[float] = None
    serving_size: Optional[str] = None
    food_items: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
