"""External food / nutrition / market data provider integrations.

The registry exposes a single entry point for the agents while keeping the
individual upstream services (USDA, Open Food Facts, Nutritionix, ...)
swappable and independently testable.
"""

from .base import (
    FoodProvider,
    NutritionFacts,
    FoodResult,
    ProviderCapability,
    ProviderError,
    ProviderTimeout,
    ProviderRateLimited,
    ProviderUnavailable,
)
from .registry import FoodProviderRegistry, get_registry

__all__ = [
    "FoodProvider",
    "NutritionFacts",
    "FoodResult",
    "ProviderCapability",
    "ProviderError",
    "ProviderTimeout",
    "ProviderRateLimited",
    "ProviderUnavailable",
    "FoodProviderRegistry",
    "get_registry",
]
