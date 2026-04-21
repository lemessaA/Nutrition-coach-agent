"""Shared contract that every external food/nutrition provider implements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class ProviderCapability(str, Enum):
    """What kind of queries a provider can satisfy."""

    LOOKUP_BY_NAME = "lookup_by_name"         # "chicken breast", "1 medium apple"
    LOOKUP_BY_BARCODE = "lookup_by_barcode"   # GTIN / UPC / EAN
    NATURAL_LANGUAGE = "natural_language"     # "2 slices of pepperoni pizza"
    RECIPE_SEARCH = "recipe_search"           # keyword -> recipe list
    PRICE_LOOKUP = "price_lookup"             # grocery / market price data


@dataclass
class NutritionFacts:
    """Normalized per-serving nutrition. All macros are grams."""

    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: Optional[float] = None
    sugar: Optional[float] = None
    sodium: Optional[float] = None  # mg
    serving_size_g: Optional[float] = None


@dataclass
class FoodResult:
    """Whatever a provider found, normalized to a single shape."""

    food_name: str
    nutrition: NutritionFacts
    source: str                              # provider name
    confidence: float = 1.0                  # 0..1, used to pick between results
    brand: Optional[str] = None
    barcode: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)  # keep upstream payload for debugging

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


class ProviderError(RuntimeError):
    """Base error raised by a provider."""


class ProviderTimeout(ProviderError):
    """The upstream request exceeded the configured timeout."""


class ProviderRateLimited(ProviderError):
    """The upstream rejected the request because we're over quota."""


class ProviderUnavailable(ProviderError):
    """The upstream is down / returned 5xx / circuit broke open."""


class FoodProvider(ABC):
    """Interface for every upstream food provider."""

    name: str
    capabilities: set[ProviderCapability]

    @abstractmethod
    async def lookup(
        self,
        *,
        query: Optional[str] = None,
        barcode: Optional[str] = None,
        quantity_g: Optional[float] = None,
    ) -> Optional[FoodResult]:
        """Return the best FoodResult for the query, or None if nothing useful."""

    async def search(
        self,
        query: str,
        limit: int = 10,
    ) -> List[FoodResult]:
        """Return multiple results for a query. Default: wrap lookup()."""
        result = await self.lookup(query=query)
        return [result] if result else []

    async def close(self) -> None:
        """Release any sockets / clients. Called on shutdown."""

    def supports(self, capability: ProviderCapability) -> bool:
        return capability in self.capabilities
