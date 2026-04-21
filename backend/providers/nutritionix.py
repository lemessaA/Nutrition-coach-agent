"""Nutritionix "Natural Nutrients" adapter.

Docs: https://developer.nutritionix.com/docs/v2
Requires an app ID and API key. Excellent for LLM-generated natural-language
queries like "2 slices of pepperoni pizza and a cup of orange juice".
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

_BASE = "https://trackapi.nutritionix.com/v2"


class NutritionixProvider(FoodProvider):
    name = "nutritionix"
    capabilities = {
        ProviderCapability.LOOKUP_BY_NAME,
        ProviderCapability.NATURAL_LANGUAGE,
    }

    def __init__(
        self,
        app_id: str,
        api_key: str,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        self._app_id = app_id
        self._api_key = api_key
        self._session = session
        self._own_session = session is None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "x-app-id": self._app_id,
                    "x-app-key": self._api_key,
                    "Content-Type": "application/json",
                },
            )
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
        session = await self._get_session()
        try:
            async with session.post(
                f"{_BASE}/natural/nutrients",
                json={"query": query},
            ) as resp:
                if resp.status == 429:
                    raise ProviderRateLimited("Nutritionix 429")
                if resp.status == 404:
                    return None
                if resp.status >= 500:
                    raise ProviderUnavailable(f"Nutritionix status {resp.status}")
                data = await resp.json()
        except aiohttp.ClientError as e:
            raise ProviderUnavailable(str(e)) from e

        foods = data.get("foods") or []
        if not foods:
            return None

        # Nutritionix returns numbers for the *parsed* quantity, not per 100g.
        # Normalize back to per-100g so downstream math stays consistent.
        first = foods[0]
        serving_g = float(first.get("serving_weight_grams") or 100.0) or 100.0
        scale = 100.0 / serving_g
        nutrition = NutritionFacts(
            calories=float(first.get("nf_calories") or 0) * scale,
            protein=float(first.get("nf_protein") or 0) * scale,
            carbs=float(first.get("nf_total_carbohydrate") or 0) * scale,
            fat=float(first.get("nf_total_fat") or 0) * scale,
            fiber=_opt(first.get("nf_dietary_fiber"), scale),
            sugar=_opt(first.get("nf_sugars"), scale),
            sodium=_opt(first.get("nf_sodium"), scale),
            serving_size_g=100.0,
        )
        return FoodResult(
            food_name=first.get("food_name", query),
            nutrition=nutrition,
            source="nutritionix",
            confidence=0.9,
            raw={"serving_qty": first.get("serving_qty"), "serving_unit": first.get("serving_unit")},
        )

    async def search(self, query: str, limit: int = 10) -> List[FoodResult]:
        # Nutritionix has a separate `/search/instant` endpoint. For now route
        # through natural-language which already handles plurals, quantities, etc.
        result = await self.lookup(query=query)
        return [result] if result else []


def _opt(v, scale: float) -> Optional[float]:
    try:
        return float(v) * scale if v is not None else None
    except (TypeError, ValueError):
        return None
