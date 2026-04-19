"""
All Pydantic schemas for the application 

"""

from .user import UserCreate, UserResponse, UserProfileCreate, UserProfileUpdate, UserProfileResponse
from .meal_plan import MealPlanCreate, MealPlanResponse
from .chat import ChatMessageCreate, ChatMessageResponse, ChatRequest, ChatResponse
from .food_analysis import FoodAnalysisRequest, FoodAnalysisResponse
from .nutrition import NutritionQuestionRequest, NutritionQuestionResponse
 
__all__ = [
    "UserCreate", "UserResponse", "UserProfileCreate", "UserProfileUpdate", "UserProfileResponse",
    "MealPlanCreate", "MealPlanResponse",
    "ChatMessageCreate", "ChatMessageResponse", "ChatRequest", "ChatResponse",
    "FoodAnalysisRequest", "FoodAnalysisResponse",
    "NutritionQuestionRequest", "NutritionQuestionResponse"
]

# __init__.py file
# This file is used to export all the schemas from the schemas directory
# to make them available for import in other parts of the application