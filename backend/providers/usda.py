"""USDA FoodData Central adapter.

Docs: https://fdc.nal.usda.gov/api-guide.html
Get a free API key at https://fdc.nal.usda.gov/api-key-signup.html
"""

from __future__ import annotations

import logging
from typing import List, Optional

import aiohttp

from .base import (
    FoodProvider,
    FoodResult,
    NutritionFacts,
    ProviderCapability,
    ProviderRateLimited,
    ProviderUnavailable,
)

logger = logging.getLogger(__name__)

_BASE = "https://api.nal.usda.gov/fdc/v1"

# Nutrient numbers used by FoodData Central.
_NUTRIENT_MAP = {
    "calories": {1008, 2047, 2048},  # Energy (kcal)
    "protein": {1003},
    "fat": {1004},
    "carbs": {1005},
    "fiber": {1079},
    "sugar": {2000},
    "sodium": {1093},  # mg
}


class USDAProvider(FoodProvider):
    name = "usda"
    capabilities = {ProviderCapability.LOOKUP_BY_NAME}

    def __init__(self, api_key: str, session: Optional[aiohttp.ClientSession] = None) -> None:
        self._api_key = api_key
        self._session = session
        self._own_session = session is None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        if self._own_session and self._session and not self._session.closed:
            await self._session.close()

    async def lookup(
        self,
        *,
        query: Optional[str] = None,
        barcode: Optional[str] = None,
        quantity_g: Optional[float] = None,
    ) -> Optional[FoodResult]:
        if not query:
            return None
        results = await self.search(query, limit=1)
        return results[0] if results else None

    async def search(self, query: str, limit: int = 10) -> List[FoodResult]:
        session = await self._get_session()
        params = {
            "api_key": self._api_key,
            "query": query,
            "pageSize": limit,
            # Prefer foundation + SR Legacy for generic (non-branded) entries first.
            "dataType": "Foundation,SR Legacy,Survey (FNDDS),Branded",
        }
        try:
            async with session.get(f"{_BASE}/foods/search", params=params) as resp:
                if resp.status == 429:
                    raise ProviderRateLimited("USDA 429 Too Many Requests")
                if resp.status >= 500:
                    raise ProviderUnavailable(f"USDA search status {resp.status}")
                data = await resp.json()
        except aiohttp.ClientError as e:
            raise ProviderUnavailable(str(e)) from e

        out: List[FoodResult] = []
        for food in (data.get("foods") or [])[:limit]:
            result = self._food_to_result(food)
            if result:
                out.append(result)
        return out

    @staticmethod
    def _food_to_result(food: dict) -> Optional[FoodResult]:
        # Collect per-100g values.
        values = {k: 0.0 for k in _NUTRIENT_MAP}
        for nut in food.get("foodNutrients") or []:
            num = nut.get("nutrientNumber")
            val = nut.get("value")
            if val is None or num is None:
                continue
            try:
                num_int = int(num)
                val_f = float(val)
            except (TypeError, ValueError):
                continue
            for macro, numbers in _NUTRIENT_MAP.items():
                if num_int in numbers:
                    values[macro] = val_f
                    break

        if values["calories"] == 0:
            return None

        nutrition = NutritionFacts(
            calories=values["calories"],
            protein=values["protein"],
            carbs=values["carbs"],
            fat=values["fat"],
            fiber=values["fiber"] or None,
            sugar=values["sugar"] or None,
            sodium=values["sodium"] or None,
            serving_size_g=100.0,
        )
        dtype = food.get("dataType")
        confidence = 0.95 if dtype in ("Foundation", "SR Legacy") else 0.8
        return FoodResult(
            food_name=food.get("description", "unknown"),
            nutrition=nutrition,
            source="usda",
            confidence=confidence,
            brand=food.get("brandName"),
            raw={"fdcId": food.get("fdcId"), "dataType": dtype},
        )
