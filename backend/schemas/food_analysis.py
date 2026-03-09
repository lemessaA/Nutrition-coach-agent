from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
"""
Food analysis related Pydantic schemas
"""

class FoodItem(BaseModel):
    name: str
    quantity: float
    unit: str
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None


class FoodAnalysisRequest(BaseModel):
    food_input: str # e.g., "1 apple", "200g chicken breast"
    serving_size: Optional[str] = None # e.g., "1 medium", "200g"


class FoodAnalysisResponse(BaseModel):
    id: int # Database ID
    user_id: int # User ID
    food_input: str # Original food input
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
