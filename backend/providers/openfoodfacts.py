"""Open Food Facts adapter.

Docs: https://openfoodfacts.github.io/openfoodfacts-server/api/
No API key required. Best for packaged products / barcode lookup.
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
    ProviderUnavailable,
)

logger = logging.getLogger(__name__)

_BASE_PRODUCT = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
_BASE_SEARCH = "https://world.openfoodfacts.org/cgi/search.pl"


class OpenFoodFactsProvider(FoodProvider):
    name = "openfoodfacts"
    capabilities = {
        ProviderCapability.LOOKUP_BY_BARCODE,
        ProviderCapability.LOOKUP_BY_NAME,
    }

    def __init__(self, session: Optional[aiohttp.ClientSession] = None) -> None:
        self._session = session
        self._own_session = session is None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"User-Agent": "nutrition-coach-agent/1.0"},
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
        if barcode:
            return await self._by_barcode(barcode)
        if query:
            results = await self.search(query, limit=1)
            return results[0] if results else None
        return None

    async def search(self, query: str, limit: int = 10) -> List[FoodResult]:
        session = await self._get_session()
        params = {
            "search_terms": query,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": limit,
        }
        try:
            async with session.get(_BASE_SEARCH, params=params) as resp:
                if resp.status >= 500:
                    raise ProviderUnavailable(f"OFF search status {resp.status}")
                data = await resp.json(content_type=None)
        except aiohttp.ClientError as e:
            raise ProviderUnavailable(str(e)) from e

        out: List[FoodResult] = []
        for product in (data.get("products") or [])[:limit]:
            result = self._product_to_result(product)
            if result:
                out.append(result)
        return out

    async def _by_barcode(self, barcode: str) -> Optional[FoodResult]:
        session = await self._get_session()
        url = _BASE_PRODUCT.format(barcode=barcode)
        try:
            async with session.get(url) as resp:
                if resp.status == 404:
                    return None
                if resp.status >= 500:
                    raise ProviderUnavailable(f"OFF product status {resp.status}")
                data = await resp.json(content_type=None)
        except aiohttp.ClientError as e:
            raise ProviderUnavailable(str(e)) from e

        product = data.get("product")
        if not product:
            return None
        return self._product_to_result(product, fallback_barcode=barcode)

    @staticmethod
    def _product_to_result(
        product: dict, fallback_barcode: Optional[str] = None
    ) -> Optional[FoodResult]:
        nutriments = product.get("nutriments") or {}
        # OFF gives values per 100g via `*_100g` keys.
        kcal = nutriments.get("energy-kcal_100g") or nutriments.get("energy-kcal_value")
        if kcal is None:
            return None
        name = (
            product.get("product_name")
            or product.get("generic_name")
            or product.get("_id")
            or "unknown"
        )
        nutrition = NutritionFacts(
            calories=float(kcal),
            protein=float(nutriments.get("proteins_100g") or 0),
            carbs=float(nutriments.get("carbohydrates_100g") or 0),
            fat=float(nutriments.get("fat_100g") or 0),
            fiber=_opt(nutriments.get("fiber_100g")),
            sugar=_opt(nutriments.get("sugars_100g")),
            sodium=_opt(nutriments.get("sodium_100g")),
            serving_size_g=100.0,
        )
        return FoodResult(
            food_name=str(name).strip(),
            nutrition=nutrition,
            source="openfoodfacts",
            confidence=0.85 if fallback_barcode else 0.7,
            brand=product.get("brands"),
            barcode=product.get("code") or fallback_barcode,
            raw={"id": product.get("_id")},
        )


def _opt(v) -> Optional[float]:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None
