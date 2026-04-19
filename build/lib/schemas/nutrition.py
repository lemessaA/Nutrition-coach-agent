from pydantic import BaseModel
from typing import Optional
from datetime import datetime
"""
Nutrition-related Pydantic schemas
"""

class NutritionQuestionRequest(BaseModel):
    question: str
    context: Optional[str] = None


class NutritionQuestionResponse(BaseModel):
    question: str
    answer: str
    category: Optional[str] = None
    source: Optional[str] = None
    confidence: Optional[float] = None
    related_questions: Optional[list] = None
