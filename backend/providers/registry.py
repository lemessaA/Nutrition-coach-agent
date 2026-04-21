"""Registry that routes a query to the right provider(s) with
cache + timeout + circuit breaker + graceful fallback.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional

from .base import (
    FoodProvider,
    FoodResult,
    ProviderCapability,
    ProviderError,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable,
)
from .cache import TTLCache

logger = logging.getLogger(__name__)


@dataclass
class _CircuitState:
    consecutive_failures: int = 0
    open_until: float = 0.0


@dataclass
class _ProviderEntry:
    provider: FoodProvider
    priority: int = 100            # lower = tried first
    timeout_s: float = 4.0
    circuit: _CircuitState = field(default_factory=_CircuitState)


class FoodProviderRegistry:
    """Fan-out query across registered providers with a sane reliability envelope."""

    def __init__(
        self,
        cache: Optional[TTLCache] = None,
        breaker_threshold: int = 3,
        breaker_cooldown_s: float = 30.0,
    ) -> None:
        self._providers: List[_ProviderEntry] = []
        self._cache = cache or TTLCache()
        self._breaker_threshold = breaker_threshold
        self._breaker_cooldown = breaker_cooldown_s

    def register(
        self,
        provider: FoodProvider,
        *,
        priority: int = 100,
        timeout_s: float = 4.0,
    ) -> None:
        self._providers.append(
            _ProviderEntry(provider=provider, priority=priority, timeout_s=timeout_s)
        )
        self._providers.sort(key=lambda e: e.priority)
        logger.info("Registered food provider '%s' (priority=%s)", provider.name, priority)

    async def close(self) -> None:
        await asyncio.gather(*(e.provider.close() for e in self._providers), return_exceptions=True)

    # ---- public API --------------------------------------------------------

    async def lookup(
        self,
        *,
        query: Optional[str] = None,
        barcode: Optional[str] = None,
        quantity_g: Optional[float] = None,
    ) -> Optional[FoodResult]:
        """Return the first successful normalized result from the priority chain."""
        capability = (
            ProviderCapability.LOOKUP_BY_BARCODE if barcode else ProviderCapability.LOOKUP_BY_NAME
        )
        cache_key = self._cache_key(capability.value, query, barcode, quantity_g)

        cached = await self._cache.get(cache_key)
        if cached is not None:
            return cached

        for entry in self._providers:
            if not entry.provider.supports(capability):
                continue
            if self._breaker_is_open(entry):
                continue

            try:
                result = await asyncio.wait_for(
                    entry.provider.lookup(query=query, barcode=barcode, quantity_g=quantity_g),
                    timeout=entry.timeout_s,
                )
            except asyncio.TimeoutError:
                self._on_failure(entry, ProviderTimeout(f"{entry.provider.name} timed out"))
                continue
            except ProviderRateLimited as e:
                logger.warning("Provider '%s' rate limited: %s", entry.provider.name, e)
                self._on_failure(entry, e, cooldown_multiplier=2.0)
                continue
            except ProviderError as e:
                self._on_failure(entry, e)
                continue
            except Exception as e:  # defensive: never let an adapter kill the agent
                self._on_failure(entry, ProviderUnavailable(str(e)))
                continue

            self._on_success(entry)
            if result:
                await self._cache.set(cache_key, result)
                return result

        return None

    async def search(self, query: str, limit: int = 10) -> List[FoodResult]:
        """Aggregate search results across all providers, dedup by name+source."""
        results: List[FoodResult] = []
        for entry in self._providers:
            if not entry.provider.supports(ProviderCapability.LOOKUP_BY_NAME):
                continue
            if self._breaker_is_open(entry):
                continue
            try:
                found = await asyncio.wait_for(
                    entry.provider.search(query=query, limit=limit),
                    timeout=entry.timeout_s,
                )
                results.extend(found)
                self._on_success(entry)
            except Exception as e:
                self._on_failure(entry, ProviderUnavailable(str(e)))
        # Rank by confidence descending; keep top `limit` unique (name, source)
        seen = set()
        ranked: List[FoodResult] = []
        for r in sorted(results, key=lambda x: x.confidence, reverse=True):
            key = (r.food_name.lower(), r.source)
            if key in seen:
                continue
            seen.add(key)
            ranked.append(r)
            if len(ranked) >= limit:
                break
        return ranked

    # ---- breaker -----------------------------------------------------------

    def _breaker_is_open(self, entry: _ProviderEntry) -> bool:
        return time.time() < entry.circuit.open_until

    def _on_success(self, entry: _ProviderEntry) -> None:
        entry.circuit.consecutive_failures = 0
        entry.circuit.open_until = 0

    def _on_failure(
        self,
        entry: _ProviderEntry,
        err: Exception,
        cooldown_multiplier: float = 1.0,
    ) -> None:
        entry.circuit.consecutive_failures += 1
        logger.warning(
            "Provider '%s' failed (%s/%s): %s",
            entry.provider.name,
            entry.circuit.consecutive_failures,
            self._breaker_threshold,
            err,
        )
        if entry.circuit.consecutive_failures >= self._breaker_threshold:
            entry.circuit.open_until = time.time() + self._breaker_cooldown * cooldown_multiplier
            logger.warning(
                "Opening circuit for provider '%s' for %.1fs",
                entry.provider.name,
                self._breaker_cooldown * cooldown_multiplier,
            )

    @staticmethod
    def _cache_key(*parts) -> str:
        return "|".join(str(p or "") for p in parts)


# ---- module-level singleton -------------------------------------------------

_REGISTRY: Optional[FoodProviderRegistry] = None


def get_registry() -> FoodProviderRegistry:
    """Return a process-wide registry, created lazily from configuration."""
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _build_default_registry()
    return _REGISTRY


def _build_default_registry() -> FoodProviderRegistry:
    """Wire up providers based on env-var config.

    Kept here (instead of in __init__) so that tests can construct their own
    registry with mock providers.
    """
    from backend.config import settings  # local import to avoid cycle at import time
    from .openfoodfacts import OpenFoodFactsProvider
    from .usda import USDAProvider
    from .nutritionix import NutritionixProvider

    reg = FoodProviderRegistry()

    # Barcode / packaged products: free, no key needed.
    if getattr(settings, "openfoodfacts_enabled", True):
        reg.register(OpenFoodFactsProvider(), priority=10)

    # Generic foods: free, needs a free API key.
    usda_key = getattr(settings, "usda_api_key", None)
    if usda_key:
        reg.register(USDAProvider(api_key=usda_key), priority=20)

    # Natural-language parsing: paid, optional.
    nix_id = getattr(settings, "nutritionix_app_id", None)
    nix_key = getattr(settings, "nutritionix_api_key", None)
    if nix_id and nix_key:
        reg.register(NutritionixProvider(app_id=nix_id, api_key=nix_key), priority=30)

    return reg
