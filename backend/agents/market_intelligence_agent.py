"""Market intelligence agent backed by real data sources.

Data sources used (all free, no partner contracts needed):
  - Open Food Facts **Prices** API  (crowdsourced grocery prices, live)
      https://prices.openfoodfacts.org/api/v1/
  - Open Food Facts **Products** API (nutrition + barcode)
      https://world.openfoodfacts.org/api/v2/
  - Local `MarketData` SQLAlchemy table (cached prices we've already fetched)

The agent still falls back to curated data when the upstream is slow/down so
the UI never shows a blank screen, but every fallback is clearly tagged with
`"source": "fallback"` so downstream consumers can decide what to do.
"""

from __future__ import annotations

import asyncio
import logging
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import aiohttp

from agents.base import BaseAgent
from database.connection import SessionLocal
from database.models import MarketData

logger = logging.getLogger(__name__)

_OFF_PRICES_BASE = "https://prices.openfoodfacts.org/api/v1"
_OFF_PRODUCTS_BASE = "https://world.openfoodfacts.org/api/v2"
_USER_AGENT = "nutrition-coach-agent/1.0 (+https://github.com/)"

# Window considered "fresh enough" to serve local cache without re-fetching.
_CACHE_MAX_AGE = timedelta(days=7)


class MarketIntelligenceAgent(BaseAgent):
    """Agent for gathering market data on food prices, availability, and trends."""

    def __init__(self) -> None:
        super().__init__("Market Intelligence Agent")
        self._session: Optional[aiohttp.ClientSession] = None

    # ------------------------------------------------------------------ infra

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"User-Agent": _USER_AGENT, "Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=6),
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    # -------------------------------------------------------------- prompt/api

    def get_system_prompt(self) -> str:
        return (
            "You are a market intelligence specialist focusing on food pricing "
            "and availability. Your role is to:\n"
            "1. Analyze food price trends and availability\n"
            "2. Provide cost-effective nutrition recommendations\n"
            "3. Suggest seasonal and locally available alternatives\n"
            "4. Help users make budget-conscious healthy choices\n"
            "5. Identify market trends affecting nutrition planning\n\n"
            "Always provide practical, actionable advice that considers both "
            "nutrition and budget. Be transparent about data limitations and "
            "regional variations."
        )

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        action = input_data.get("action", "search")
        dispatch = {
            "search_prices": self.search_food_prices,
            "availability_check": self.check_availability,
            "seasonal_recommendations": self.get_seasonal_recommendations,
            "budget_analysis": self.analyze_budget_options,
            "market_trends": self.get_market_trends,
            "ingest_data": self.ingest_market_data,
        }
        handler = dispatch.get(action)
        if not handler:
            return {"error": f"Unknown action: {action}"}
        return await handler(input_data)

    # ==================================================================
    #  Public actions
    # ==================================================================

    async def search_food_prices(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Search for current food prices across local cache + Open Food Facts."""
        food_items: List[str] = input_data.get("food_items") or []
        location: str = input_data.get("location") or "general"
        price_range: str = input_data.get("price_range") or "all"

        if not food_items:
            return {"error": "Food items are required for price search"}

        price_results: List[Dict[str, Any]] = []
        for item in food_items:
            cached = self._search_local_prices(item, location)
            if cached:
                price_results.append(cached)
                continue

            external = await self._search_external_prices(item)
            price_results.append(external)

            if external.get("price"):
                self._store_market_data(external)

        price_analysis = self._analyze_price_trends(price_results)
        alternatives = self._suggest_alternatives(food_items, price_results, price_range)

        return {
            "success": True,
            "food_items": food_items,
            "location": location,
            "price_results": price_results,
            "price_analysis": price_analysis,
            "alternatives": alternatives,
            "search_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def check_availability(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        food_items: List[str] = input_data.get("food_items") or []
        location: str = input_data.get("location") or "general"
        season: str = input_data.get("season") or _current_season()

        availability_results: List[Dict[str, Any]] = []
        for item in food_items:
            availability_results.append(
                await self._check_item_availability(item, location, season)
            )

        insights = self._generate_availability_insights(availability_results)

        return {
            "success": True,
            "food_items": food_items,
            "location": location,
            "season": season,
            "availability_results": availability_results,
            "insights": insights,
            "check_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_seasonal_recommendations(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        season: str = input_data.get("season") or _current_season()
        location: str = input_data.get("location") or "general"
        user_preferences: Dict[str, Any] = input_data.get("user_preferences") or {}

        seasonal_produce = self._get_seasonal_produce(season, location)

        # Enrich each produce entry with a live price snapshot.
        await asyncio.gather(
            *(self._enrich_with_price(item) for item in seasonal_produce),
            return_exceptions=True,
        )

        filtered_produce = self._filter_by_preferences(seasonal_produce, user_preferences)
        nutritional_benefits = self._analyze_nutritional_benefits(filtered_produce)
        recipe_suggestions = self._suggest_seasonal_recipes(filtered_produce, season)

        return {
            "success": True,
            "season": season,
            "location": location,
            "seasonal_produce": filtered_produce,
            "nutritional_benefits": nutritional_benefits,
            "recipe_suggestions": recipe_suggestions,
            "recommendation_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def analyze_budget_options(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        budget: float = float(input_data.get("budget") or 0)
        dietary_requirements: Dict[str, Any] = input_data.get("dietary_requirements") or {}
        family_size: int = int(input_data.get("family_size") or 1)
        time_period: str = input_data.get("time_period") or "week"

        budget_options = await self._get_budget_options(budget, dietary_requirements, family_size)
        cost_analysis = self._calculate_cost_per_meal(budget_options, family_size, time_period)
        meal_suggestions = self._generate_budget_meal_plan(budget_options, dietary_requirements)
        shopping_tips = self._generate_budget_shopping_tips(budget_options)

        return {
            "success": True,
            "budget": budget,
            "family_size": family_size,
            "time_period": time_period,
            "budget_options": budget_options,
            "cost_analysis": cost_analysis,
            "meal_suggestions": meal_suggestions,
            "shopping_tips": shopping_tips,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_market_trends(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        trend_category: str = input_data.get("category", "general")
        time_frame: str = input_data.get("time_frame", "month")

        trends = await self._analyze_market_trends(trend_category, time_frame)
        insights = self._generate_trend_insights(trends)
        predictions = self._predict_future_trends(trends)

        return {
            "success": True,
            "category": trend_category,
            "time_frame": time_frame,
            "trends": trends,
            "insights": insights,
            "predictions": predictions,
            "trend_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def ingest_market_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        data_source = input_data.get("data_source", "manual")
        data_format = input_data.get("data_format", "json")
        market_data = input_data.get("market_data") or {}

        cleaned = self._validate_and_clean_data(market_data, data_format)
        records = cleaned if isinstance(cleaned, list) else [cleaned]

        stored = 0
        for record in records:
            if record.get("food_item") and record.get("price"):
                self._store_market_data(
                    {
                        "item": record["food_item"],
                        "price": float(record["price"]),
                        "unit": record.get("unit") or "unit",
                        "location": record.get("location") or "general",
                        "source": record.get("source") or data_source,
                        "availability": record.get("availability") or "in_stock",
                    }
                )
                stored += 1

        return {
            "success": True,
            "data_source": data_source,
            "records_processed": stored,
            "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ==================================================================
    #  Real price lookup
    # ==================================================================

    def _search_local_prices(self, item: str, location: str) -> Optional[Dict[str, Any]]:
        """Look up a recent price in the `market_data` table."""
        db = SessionLocal()
        try:
            q = (
                db.query(MarketData)
                .filter(MarketData.food_item.ilike(f"%{item.lower()}%"))
                .order_by(MarketData.updated_at.desc().nullslast(), MarketData.created_at.desc())
            )
            if location and location != "general":
                q = q.filter(MarketData.location.ilike(f"%{location}%"))
            row: Optional[MarketData] = q.first()
            if not row:
                return None
            last = row.updated_at or row.created_at
            if last and last.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc) - _CACHE_MAX_AGE:
                return None
            return {
                "item": row.food_item,
                "location": row.location or location,
                "price": row.price,
                "unit": row.unit,
                "source": row.source or "local_database",
                "last_updated": (last.isoformat() if last else None),
                "availability": "in_stock" if row.in_stock else "out_of_stock",
                "is_seasonal": bool(row.seasonal),
            }
        except Exception as e:
            logger.warning("Local market_data lookup failed for '%s': %s", item, e)
            return None
        finally:
            db.close()

    async def _search_external_prices(self, item: str) -> Dict[str, Any]:
        """Hit Open Food Facts Prices API for a live price snapshot."""
        try:
            session = await self._get_session()
            params = {
                "product_name_like": item,
                "page_size": 25,
                "order_by": "-date",
            }
            async with session.get(f"{_OFF_PRICES_BASE}/prices", params=params) as resp:
                if resp.status >= 500:
                    raise RuntimeError(f"OFF prices status {resp.status}")
                data = await resp.json(content_type=None)

            items = data.get("items") or []
            prices = [float(p["price"]) for p in items if isinstance(p.get("price"), (int, float))]
            if not prices:
                return {
                    "item": item,
                    "location": "national_average",
                    "price": None,
                    "unit": "unit",
                    "source": "openfoodfacts-prices",
                    "availability": "unknown",
                    "note": "No live price data found for this item",
                }

            median_price = round(statistics.median(prices), 2)
            currency = _majority(p.get("currency") for p in items) or "USD"
            locations = [
                (p.get("location") or {}).get("osm_address_country") for p in items
            ]
            country = _majority(locations) or "multi-region"
            brands = _majority(
                (p.get("product") or {}).get("brands") for p in items
            )
            last = max(
                (p.get("updated") or p.get("created") or "" for p in items),
                default="",
            )

            return {
                "item": item,
                "location": country,
                "price": median_price,
                "price_range": {"min": round(min(prices), 2), "max": round(max(prices), 2)},
                "samples": len(prices),
                "currency": currency,
                "unit": "unit",
                "source": "openfoodfacts-prices",
                "brands": brands,
                "last_updated": last or datetime.now(timezone.utc).isoformat(),
                "availability": "in_stock",
            }
        except asyncio.TimeoutError:
            return {"item": item, "error": "upstream timeout", "source": "openfoodfacts-prices"}
        except Exception as e:
            logger.warning("OFF prices lookup failed for '%s': %s", item, e)
            return {
                "item": item,
                "error": f"Could not fetch price data: {e}",
                "source": "openfoodfacts-prices",
            }

    def _store_market_data(self, record: Dict[str, Any]) -> None:
        """Upsert a price snapshot into the `market_data` table."""
        price = record.get("price")
        if price is None:
            return
        db = SessionLocal()
        try:
            row = (
                db.query(MarketData)
                .filter(
                    MarketData.food_item == record["item"],
                    MarketData.location == (record.get("location") or "general"),
                    MarketData.source == (record.get("source") or "openfoodfacts-prices"),
                )
                .first()
            )
            if row:
                row.price = float(price)
                row.unit = record.get("unit") or row.unit or "unit"
                row.in_stock = (record.get("availability") or "in_stock") == "in_stock"
                row.seasonal = bool(record.get("is_seasonal", row.seasonal))
            else:
                row = MarketData(
                    food_item=record["item"],
                    price=float(price),
                    unit=record.get("unit") or "unit",
                    location=record.get("location") or "general",
                    source=record.get("source") or "openfoodfacts-prices",
                    in_stock=(record.get("availability") or "in_stock") == "in_stock",
                    seasonal=bool(record.get("is_seasonal", False)),
                )
                db.add(row)
            db.commit()
        except Exception as e:
            logger.warning("Failed to persist market_data for '%s': %s", record.get("item"), e)
            db.rollback()
        finally:
            db.close()

    # ==================================================================
    #  Real trend analysis
    # ==================================================================

    async def _analyze_market_trends(
        self, category: str, time_frame: str
    ) -> List[Dict[str, Any]]:
        """Compute price-movement trends from live OFF Prices data.

        Approach:
          * Pull a large sample of the newest price entries.
          * Bucket by the product's primary (English) category tag.
          * For each bucket, compare median prices in the latest window vs.
            the prior window of the same length and report the delta.
        """
        window_days = {"week": 7, "month": 30, "quarter": 90, "year": 180}.get(time_frame, 30)

        items = await self._fetch_recent_price_items(pages=3, page_size=100)
        if not items:
            return self._fallback_trends()

        now = datetime.now(timezone.utc)
        recent_cutoff = now - timedelta(days=window_days)
        prior_cutoff = now - timedelta(days=window_days * 2)

        # Bucket by category tag (en:plant-based-foods -> "plant-based foods").
        buckets: Dict[str, Dict[str, List[float]]] = defaultdict(
            lambda: {"recent": [], "prior": []}
        )
        category_filter = (category or "").lower().strip()
        for it in items:
            ts = _parse_iso(it.get("updated") or it.get("created"))
            price = it.get("price")
            if not isinstance(price, (int, float)) or ts is None:
                continue
            product = it.get("product") or {}
            tags = product.get("categories_tags") or []
            label = _human_category(tags)
            if not label:
                continue
            if category_filter and category_filter not in label.lower() and category_filter != "general" and category_filter != "all":
                continue
            if ts >= recent_cutoff:
                buckets[label]["recent"].append(float(price))
            elif ts >= prior_cutoff:
                buckets[label]["prior"].append(float(price))

        trends: List[Dict[str, Any]] = []
        for label, samples in buckets.items():
            if len(samples["recent"]) < 3 or len(samples["prior"]) < 3:
                continue
            recent_med = statistics.median(samples["recent"])
            prior_med = statistics.median(samples["prior"])
            if prior_med <= 0:
                continue
            growth_pct = ((recent_med - prior_med) / prior_med) * 100
            trends.append(
                {
                    "trend": label,
                    "growth": f"{growth_pct:+.1f}%",
                    "description": (
                        f"Median price in this category moved from "
                        f"{prior_med:.2f} to {recent_med:.2f} over the last "
                        f"{window_days} days ({len(samples['recent'])} recent "
                        f"samples)."
                    ),
                    "recent_median": round(recent_med, 2),
                    "prior_median": round(prior_med, 2),
                    "samples": len(samples["recent"]),
                }
            )

        # Rank by activity × |growth| so the UI surfaces meaningful movers.
        trends.sort(key=lambda t: abs(_growth_num(t["growth"])) * t["samples"], reverse=True)
        top = trends[:6]
        if not top:
            return self._fallback_trends()
        return top

    async def _fetch_recent_price_items(
        self, pages: int = 2, page_size: int = 100
    ) -> List[Dict[str, Any]]:
        session = await self._get_session()
        all_items: List[Dict[str, Any]] = []
        for page in range(1, pages + 1):
            try:
                async with session.get(
                    f"{_OFF_PRICES_BASE}/prices",
                    params={"page": page, "page_size": page_size, "order_by": "-date"},
                ) as resp:
                    if resp.status != 200:
                        break
                    data = await resp.json(content_type=None)
            except Exception as e:
                logger.warning("OFF prices pagination failed (page=%s): %s", page, e)
                break
            batch = data.get("items") or []
            if not batch:
                break
            all_items.extend(batch)
        return all_items

    def _fallback_trends(self) -> List[Dict[str, Any]]:
        """Used only when the upstream is unreachable. Clearly labeled."""
        return [
            {
                "trend": "Plant-based foods",
                "growth": "+0.0%",
                "description": "Live market data unavailable — showing baseline trend set.",
                "samples": 0,
                "source": "fallback",
            },
            {
                "trend": "Local sourcing",
                "growth": "+0.0%",
                "description": "Live market data unavailable — showing baseline trend set.",
                "samples": 0,
                "source": "fallback",
            },
        ]

    def _generate_trend_insights(self, trends: List[Dict[str, Any]]) -> List[str]:
        return [
            f"{t['trend']}: {t['description']}".strip()
            for t in trends
            if t.get("trend")
        ]

    def _predict_future_trends(self, trends: List[Dict[str, Any]]) -> List[str]:
        """Derive a short forecast by extrapolating observed deltas."""
        predictions: List[str] = []
        for t in trends[:3]:
            pct = _growth_num(t.get("growth", "0"))
            direction = "keep rising" if pct > 2 else "keep cooling" if pct < -2 else "stabilize"
            predictions.append(
                f"{t['trend']} is expected to {direction} into next period "
                f"(recent change {pct:+.1f}%)."
            )
        if not predictions:
            predictions = [
                "Insufficient live data to project category movement; will refresh on next tick."
            ]
        return predictions

    # ==================================================================
    #  Seasonal / budget / availability helpers (mostly local, now
    #  enriched with live price data where possible).
    # ==================================================================

    async def _check_item_availability(
        self, item: str, location: str, season: str
    ) -> Dict[str, Any]:
        local = self._search_local_prices(item, location)
        if local:
            return {
                "item": item,
                "location": location,
                "season": season,
                "availability": local.get("availability", "in_stock"),
                "is_seasonal": local.get("is_seasonal", False),
                "quality": "good",
                "price": local.get("price"),
                "source": local.get("source"),
                "last_updated": local.get("last_updated"),
            }
        external = await self._search_external_prices(item)
        seasonal_set = _season_produce()
        is_seasonal = item.lower() in seasonal_set.get(season, set())
        return {
            "item": item,
            "location": location,
            "season": season,
            "availability": external.get("availability", "unknown"),
            "is_seasonal": is_seasonal,
            "quality": "excellent" if is_seasonal else "good",
            "price": external.get("price"),
            "samples": external.get("samples"),
            "source": external.get("source"),
            "last_updated": external.get("last_updated"),
        }

    def _generate_availability_insights(
        self, availability_results: List[Dict[str, Any]]
    ) -> List[str]:
        out: List[str] = []
        for r in availability_results:
            item = r.get("item")
            price = r.get("price")
            if price is not None:
                out.append(
                    f"{item}: {r.get('availability', 'unknown')} at ~{price} "
                    f"({r.get('source')})."
                )
            else:
                out.append(
                    f"{item}: {r.get('availability', 'unknown')} — no live price data."
                )
        return out

    def _get_seasonal_produce(self, season: str, location: str) -> List[Dict[str, Any]]:
        produce = _season_produce_data().get(season, _season_produce_data()["spring"])
        return [dict(p) for p in produce]

    async def _enrich_with_price(self, produce_item: Dict[str, Any]) -> None:
        """Attach a live median price from OFF Prices, when possible."""
        try:
            quote = await self._search_external_prices(produce_item.get("name", ""))
            if quote.get("price") is not None:
                produce_item["market_price"] = quote["price"]
                produce_item["currency"] = quote.get("currency")
                produce_item["price_source"] = quote.get("source")
                produce_item["price_samples"] = quote.get("samples")
        except Exception:
            # non-fatal — keep the static produce entry
            return

    def _filter_by_preferences(
        self, produce: List[Dict[str, Any]], preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        if not preferences:
            return produce
        return [p for p in produce]  # placeholder for real filters

    def _analyze_nutritional_benefits(self, produce: List[Dict[str, Any]]) -> Dict[str, Any]:
        all_nutrients: List[str] = []
        for p in produce:
            all_nutrients.extend(p.get("nutrients", []))
        c = Counter(all_nutrients)
        return {
            "top_nutrients": c.most_common(5),
            "total_variety": len(c),
            "seasonal_advantage": "Peak nutritional content and flavor",
        }

    def _suggest_seasonal_recipes(
        self, produce: List[Dict[str, Any]], season: str
    ) -> List[str]:
        names = {p["name"] for p in produce}
        recipes: List[str] = []
        if {"tomatoes", "corn"} & names == {"tomatoes", "corn"}:
            recipes.append("Summer vegetable salad with grilled corn")
        if "pumpkin" in names:
            recipes.append("Roasted pumpkin soup")
        if {"apples", "brussels sprouts"} & names == {"apples", "brussels sprouts"}:
            recipes.append("Apple Brussels sprouts slaw")
        if "kale" in names:
            recipes.append("Winter kale and citrus salad")
        return recipes[:3]

    async def _get_budget_options(
        self, budget: float, requirements: Dict[str, Any], family_size: int
    ) -> List[Dict[str, Any]]:
        categories = [
            ("proteins", 0.3, ["eggs", "beans", "chicken thighs", "canned fish"]),
            ("vegetables", 0.25, ["frozen vegetables", "carrots", "cabbage"]),
            ("grains", 0.2, ["rice", "oats", "pasta", "potatoes"]),
        ]
        out: List[Dict[str, Any]] = []
        for name, share, options in categories:
            priced: List[Dict[str, Any]] = []
            for opt in options:
                quote = await self._search_external_prices(opt)
                priced.append(
                    {
                        "name": opt,
                        "market_price": quote.get("price"),
                        "currency": quote.get("currency"),
                        "samples": quote.get("samples"),
                    }
                )
            out.append(
                {
                    "category": name,
                    "options": priced,
                    "weekly_cost": round((budget or 0) * share, 2),
                    "servings": family_size * 7,
                }
            )
        return out

    def _calculate_cost_per_meal(
        self,
        budget_options: List[Dict[str, Any]],
        family_size: int,
        time_period: str,
    ) -> Dict[str, Any]:
        total = sum(option["weekly_cost"] for option in budget_options)
        meals_per_week = family_size * 21
        cost_per_meal = (total / meals_per_week) if meals_per_week else 0
        return {
            "total_weekly_cost": round(total, 2),
            "meals_per_week": meals_per_week,
            "cost_per_meal": round(cost_per_meal, 2),
            "cost_per_person_per_day": round((total / family_size / 7) if family_size else 0, 2),
        }

    def _generate_budget_meal_plan(
        self, budget_options: List[Dict[str, Any]], requirements: Dict[str, Any]
    ) -> List[str]:
        return [
            "Breakfast: Oatmeal with seasonal fruit",
            "Lunch: Bean and vegetable soup",
            "Dinner: Chicken thighs with roasted vegetables",
            "Snacks: Hard-boiled eggs and seasonal fruit",
        ]

    def _generate_budget_shopping_tips(
        self, budget_options: List[Dict[str, Any]]
    ) -> List[str]:
        return [
            "Buy seasonal produce for best prices and quality",
            "Consider frozen vegetables for convenience and nutrition",
            "Purchase whole grains in bulk for savings",
            "Plan meals around sales and specials",
            "Reduce food waste by using leftovers creatively",
        ]

    def _analyze_price_trends(self, price_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        prices = [r.get("price") for r in price_results if isinstance(r.get("price"), (int, float))]
        if not prices:
            return {"trend": "no_data", "analysis": "No valid price data"}
        return {
            "trend": "stable",
            "average_price": round(sum(prices) / len(prices), 2),
            "price_range": {"min": min(prices), "max": max(prices)},
            "data_points": len(prices),
        }

    def _suggest_alternatives(
        self,
        food_items: List[str],
        price_results: List[Dict[str, Any]],
        price_range: str,
    ) -> List[Dict[str, Any]]:
        alternatives_map = {
            "salmon": ["canned salmon", "mackerel", "sardines"],
            "beef": ["chicken", "turkey", "pork"],
            "fresh berries": ["frozen berries", "apples", "bananas"],
        }
        out: List[Dict[str, Any]] = []
        for item in food_items:
            for alt in alternatives_map.get(item.lower(), []):
                out.append(
                    {
                        "original_item": item,
                        "alternative": alt,
                        "reason": "More budget-friendly option",
                        "estimated_savings": "20-30%",
                    }
                )
        return out

    def _validate_and_clean_data(self, data: Any, format_type: str) -> Any:
        if format_type != "json":
            return data
        if isinstance(data, list):
            return [self._validate_and_clean_data(d, format_type) for d in data]
        if not isinstance(data, dict):
            raise ValueError("Invalid JSON format")
        required_fields = ["food_item", "price", "unit"]
        for field in required_fields:
            data.setdefault(field, None)
        return data


# =====================================================================
#  Module-level utilities
# =====================================================================


def _current_season(dt: Optional[datetime] = None) -> str:
    """Return the meteorological season for the given (or current) UTC date."""
    m = (dt or datetime.now(timezone.utc)).month
    if m in (3, 4, 5):
        return "spring"
    if m in (6, 7, 8):
        return "summer"
    if m in (9, 10, 11):
        return "fall"
    return "winter"


def _season_produce() -> Dict[str, set]:
    return {k: {p["name"] for p in v} for k, v in _season_produce_data().items()}


def _season_produce_data() -> Dict[str, List[Dict[str, Any]]]:
    return {
        "spring": [
            {"name": "asparagus", "nutrients": ["folate", "vitamin K"], "price": "moderate"},
            {"name": "strawberries", "nutrients": ["vitamin C", "fiber"], "price": "low"},
            {"name": "spinach", "nutrients": ["iron", "vitamin A"], "price": "low"},
        ],
        "summer": [
            {"name": "tomatoes", "nutrients": ["lycopene", "vitamin C"], "price": "low"},
            {"name": "corn", "nutrients": ["fiber", "B vitamins"], "price": "low"},
            {"name": "watermelon", "nutrients": ["vitamin A", "hydration"], "price": "low"},
        ],
        "fall": [
            {"name": "pumpkin", "nutrients": ["vitamin A", "fiber"], "price": "low"},
            {"name": "apples", "nutrients": ["fiber", "vitamin C"], "price": "low"},
            {"name": "brussels sprouts", "nutrients": ["vitamin K", "vitamin C"], "price": "moderate"},
        ],
        "winter": [
            {"name": "squash", "nutrients": ["vitamin A", "fiber"], "price": "low"},
            {"name": "citrus", "nutrients": ["vitamin C", "folate"], "price": "moderate"},
            {"name": "kale", "nutrients": ["vitamin K", "vitamin A"], "price": "low"},
        ],
    }


def _majority(values) -> Optional[str]:
    filtered = [v for v in values if v]
    if not filtered:
        return None
    return Counter(filtered).most_common(1)[0][0]


def _parse_iso(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        # Python's fromisoformat doesn't accept the trailing "Z" prior to 3.11
        # in all build flavors — normalise explicitly.
        s2 = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s2)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def _human_category(tags: List[str]) -> Optional[str]:
    """Pick the most descriptive English category tag and humanize it."""
    if not tags:
        return None
    english = [t for t in tags if t.startswith("en:")]
    if not english:
        return None
    # Prefer the most specific tag (usually the last one).
    raw = english[-1][len("en:") :]
    # Drop uninformative umbrella categories.
    skip = {
        "plant-based-foods",
        "plant-based-foods-and-beverages",
        "snacks",
        "sweet-snacks",
    }
    if raw in skip and len(english) >= 2:
        raw = english[-2][len("en:") :]
    return raw.replace("-", " ")


def _growth_num(growth: Any) -> float:
    s = str(growth or "0").replace("%", "").replace("+", "").strip()
    try:
        return float(s)
    except ValueError:
        return 0.0
