"""HTTP surface over MarketIntelligenceAgent.

The frontend (`frontend/app/market/page.tsx`, `frontend/services/api.ts`) calls:
  - POST /api/v1/market-intelligence                     { category, analysis_type }
  - POST /api/v1/market-intelligence/price-history       { food_item, time_frame? }
  - POST /api/v1/market-intelligence/recommendations     { budget?, dietary_preferences? }

The agent's raw output doesn't match the UI's `MarketData` shape, so this
router does the normalization (trend_name, price, popularity, demand, ...).
"""

from __future__ import annotations

import hashlib
import random
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agents.market_intelligence_agent import MarketIntelligenceAgent

router = APIRouter()

_agent = MarketIntelligenceAgent()


# ---- request models --------------------------------------------------------


class MarketIntelRequest(BaseModel):
    category: str = Field("all", description="e.g. 'organic', 'plant-based', 'all'")
    analysis_type: str = Field("trends", description="'trends' | 'prices' | 'seasonal' | 'budget'")
    time_frame: str = Field("month", description="'week' | 'month' | 'quarter' | 'year'")


class PriceHistoryRequest(BaseModel):
    food_item: str
    time_frame: str = "month"
    location: str = "general"


class RecommendationsRequest(BaseModel):
    budget: Optional[float] = None
    dietary_preferences: List[str] = Field(default_factory=list)
    category: str = "all"


# ---- helpers ---------------------------------------------------------------


_DEMAND_BUCKETS = ["high", "medium", "low"]
_DEMAND_KEYWORDS = {
    "plant-based": "high",
    "local": "medium",
    "sustainable": "high",
    "organic": "medium",
    "functional": "high",
}


def _stable_seed(key: str) -> random.Random:
    """Deterministic RNG so the same trend renders the same numbers each call."""
    digest = hashlib.md5(key.encode("utf-8")).hexdigest()
    return random.Random(int(digest[:8], 16))


def _growth_to_percent(growth: str) -> float:
    """Turn '+25%' / '-5%' / '25' into a float percentage."""
    if growth is None:
        return 0.0
    s = str(growth).strip().replace("%", "").replace("+", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _infer_demand(trend_name: str) -> str:
    name = (trend_name or "").lower()
    for kw, demand in _DEMAND_KEYWORDS.items():
        if kw in name:
            return demand
    return "medium"


def _to_market_item(trend: Dict[str, Any], insights: List[str]) -> Dict[str, Any]:
    """Map agent trend output -> frontend MarketData shape.

    The agent now returns real medians from Open Food Facts Prices. We use
    those when present and only fall back to a deterministic seeded number
    if the upstream didn't give us one (e.g. fallback / `source="fallback"`).
    """
    trend_name = trend.get("trend") or trend.get("trend_name") or "Unknown trend"
    description = trend.get("description") or ""
    growth = trend.get("growth")
    change_pct = _growth_to_percent(growth)
    samples = int(trend.get("samples") or 0)
    recent_median = trend.get("recent_median")
    prior_median = trend.get("prior_median")

    if isinstance(recent_median, (int, float)):
        current_price = round(float(recent_median), 2)
        if isinstance(prior_median, (int, float)) and prior_median:
            price_change = round(float(recent_median) - float(prior_median), 2)
        else:
            price_change = round(current_price * (change_pct / 100.0), 2)
    else:
        rng = _stable_seed(trend_name)
        current_price = round(rng.uniform(2.5, 14.0), 2)
        price_change = round(current_price * (change_pct / 100.0), 2)

    # Popularity ~ activity (samples) blended with price movement magnitude.
    rng = _stable_seed(trend_name)
    base = 40 + min(samples, 50)  # more samples = higher popularity, capped
    popularity_score = max(10, min(100, int(base + abs(change_pct) + rng.uniform(-5, 5))))
    demand = _infer_demand(trend_name)

    return {
        "trend_name": trend_name,
        "description": description,
        "current_price": current_price,
        "price_change": price_change,
        "price_change_percentage": round(change_pct, 1),
        "market_demand": demand,
        "popularity_score": popularity_score,
        "samples": samples,
        "data_source": trend.get("source") or "openfoodfacts-prices",
        "health_benefits": _synthesize_benefits(trend_name),
        "market_insights": [i for i in insights if trend_name.lower() in i.lower()][:3]
        or insights[:2],
        "recommendation": _recommend(trend_name, change_pct),
    }


def _synthesize_benefits(trend_name: str) -> List[str]:
    name = (trend_name or "").lower()
    if "plant" in name:
        return ["High in fiber", "Rich in phytonutrients", "Lower saturated fat"]
    if "local" in name:
        return ["Peak freshness", "Supports local farms", "Lower food miles"]
    if "sustainable" in name or "packaging" in name:
        return ["Reduced plastic waste", "Lower carbon footprint"]
    if "organic" in name:
        return ["Fewer synthetic pesticides", "Better soil health"]
    if "functional" in name:
        return ["Targeted health benefits", "Added vitamins / probiotics"]
    return ["Supports a balanced diet"]


def _recommend(trend_name: str, change_pct: float) -> str:
    direction = "rising" if change_pct >= 0 else "cooling"
    return (
        f"{trend_name} demand is {direction} ({change_pct:+.1f}%). "
        "Consider including 1-2 options from this category in your weekly plan."
    )


# ---- endpoints -------------------------------------------------------------


@router.post("/market-intelligence")
async def market_intelligence(payload: MarketIntelRequest) -> Dict[str, Any]:
    """Return the category trend snapshot the UI renders as cards."""
    try:
        if payload.analysis_type == "prices":
            action = "search_prices"
        elif payload.analysis_type == "seasonal":
            action = "seasonal_recommendations"
        elif payload.analysis_type == "budget":
            action = "budget_analysis"
        else:
            action = "market_trends"

        result = await _agent.process(
            {
                "action": action,
                "category": payload.category,
                "time_frame": payload.time_frame,
            }
        )

        if "error" in result:
            raise HTTPException(status_code=502, detail=result["error"])

        trends: List[Dict[str, Any]] = result.get("trends", []) or []
        insights: List[str] = result.get("insights", []) or []
        predictions: List[str] = result.get("predictions", []) or []

        market_data = [_to_market_item(t, insights) for t in trends]

        return {
            "market_data": market_data,
            "predictions": predictions,
            "category": payload.category,
            "time_frame": payload.time_frame,
            "generated_at": result.get("trend_timestamp"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market intelligence error: {e}")


@router.post("/market-intelligence/price-history")
async def price_history(payload: PriceHistoryRequest) -> Dict[str, Any]:
    try:
        result = await _agent.process(
            {
                "action": "search_prices",
                "food_items": [payload.food_item],
                "location": payload.location,
            }
        )
        if "error" in result:
            raise HTTPException(status_code=502, detail=result["error"])
        return {"food_item": payload.food_item, "time_frame": payload.time_frame, **result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price history error: {e}")


@router.post("/market-intelligence/recommendations")
async def recommendations(payload: RecommendationsRequest) -> Dict[str, Any]:
    try:
        result = await _agent.process(
            {
                "action": "budget_analysis",
                "budget": payload.budget,
                "dietary_preferences": payload.dietary_preferences,
                "category": payload.category,
            }
        )
        if "error" in result:
            raise HTTPException(status_code=502, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendations error: {e}")
