"""Pydantic schemas for the marketplace (food seller / buyer e-commerce)."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from database.models import OrderStatusEnum


# ---------------------------------------------------------------------------
# Listings
# ---------------------------------------------------------------------------

class NutritionPayload(BaseModel):
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None
    sugar: Optional[float] = None
    sodium: Optional[float] = None


class FoodListingBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = None
    image_url: Optional[str] = None
    price: float = Field(..., ge=0)
    unit: str = Field("serving", min_length=1, max_length=32)
    stock: int = Field(0, ge=0)
    serving_size: Optional[str] = None
    tags: List[str] = []
    # Nutrition (per unit/serving)
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None
    sugar: Optional[float] = None
    sodium: Optional[float] = None


class FoodListingCreate(FoodListingBase):
    pass


class FoodListingUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = None
    image_url: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = Field(None, min_length=1, max_length=32)
    stock: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    serving_size: Optional[str] = None
    tags: Optional[List[str]] = None
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None
    sugar: Optional[float] = None
    sodium: Optional[float] = None


class FoodListingResponse(FoodListingBase):
    id: int
    seller_id: int
    seller_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

class OrderItemCreate(BaseModel):
    listing_id: int
    quantity: int = Field(..., ge=1)


class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(..., min_length=1)
    notes: Optional[str] = None
    nutrient_target: Optional[NutritionPayload] = None


class OrderItemResponse(BaseModel):
    id: int
    listing_id: int
    name_snapshot: str
    unit_price: float
    quantity: int

    # Enriched from the (still existing) listing so the UI can show nutrition.
    listing_image_url: Optional[str] = None
    listing_nutrition: Optional[NutritionPayload] = None
    listing_tags: List[str] = []

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    buyer_id: int
    seller_id: int
    buyer_name: Optional[str] = None
    seller_name: Optional[str] = None
    status: str
    total_price: float
    notes: Optional[str] = None
    nutrient_target: Optional[NutritionPayload] = None
    items: List[OrderItemResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: OrderStatusEnum


class ListingSearchParams(BaseModel):
    q: Optional[str] = None
    tags: Optional[List[str]] = None
    min_protein: Optional[float] = None
    max_sugar: Optional[float] = None
    min_fiber: Optional[float] = None
    max_calories: Optional[float] = None
    max_price: Optional[float] = None
    in_stock_only: bool = True
    sort_by: str = "newest"  # newest | protein_per_dollar | price_asc | price_desc
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


# ---------------------------------------------------------------------------
# Role management
# ---------------------------------------------------------------------------

class RoleUpdate(BaseModel):
    role: str = Field(..., pattern="^(buyer|seller|both)$")
