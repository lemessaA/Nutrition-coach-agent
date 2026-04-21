from .chat import router as chat_router
from .profile import router as profile_router
from .meal_plan import router as meal_plan_router
from .analyze_food import router as analyze_food_router
from .foods import router as foods_router
from .market import router as market_router

__all__ = [
    "chat_router",
    "profile_router",
    "meal_plan_router",
    "analyze_food_router",
    "foods_router",
    "market_router",
]
