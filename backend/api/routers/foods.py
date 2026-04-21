"""Thin HTTP surface over the multi-provider registry.

Lets the frontend:
  - resolve a food by name          GET  /api/v1/foods/search?q=chicken breast
  - scan a barcode                  GET  /api/v1/foods/barcode/{code}
  - ingest a natural-language meal  POST /api/v1/foods/natural {"query": "..."}

All three hit the cached registry so realtime calls stay cheap.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from providers import get_registry

router = APIRouter()


class NaturalQuery(BaseModel):
    query: str


def _result_to_json(result) -> Dict[str, Any]:
    return {
        "food_name": result.food_name,
        "source": result.source,
        "confidence": result.confidence,
        "brand": result.brand,
        "barcode": result.barcode,
        "nutrition_per_100g": {
            "calories": result.nutrition.calories,
            "protein": result.nutrition.protein,
            "carbs": result.nutrition.carbs,
            "fat": result.nutrition.fat,
            "fiber": result.nutrition.fiber,
            "sugar": result.nutrition.sugar,
            "sodium": result.nutrition.sodium,
        },
    }


@router.get("/foods/search")
async def search_foods(
    q: str = Query(..., min_length=1, description="Free-text food query"),
    limit: int = Query(10, ge=1, le=50),
) -> Dict[str, List[Dict[str, Any]]]:
    registry = get_registry()
    results = await registry.search(query=q, limit=limit)
    return {"results": [_result_to_json(r) for r in results]}


@router.get("/foods/barcode/{barcode}")
async def lookup_barcode(barcode: str) -> Dict[str, Any]:
    registry = get_registry()
    result = await registry.lookup(barcode=barcode)
    if not result:
        raise HTTPException(status_code=404, detail=f"Barcode '{barcode}' not found")
    return _result_to_json(result)


@router.post("/foods/natural")
async def natural_query(payload: NaturalQuery) -> Dict[str, Any]:
    registry = get_registry()
    result = await registry.lookup(query=payload.query)
    if not result:
        raise HTTPException(status_code=404, detail="No provider recognised that query")
    return _result_to_json(result)
