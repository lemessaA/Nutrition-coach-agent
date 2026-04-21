"""Marketplace router: food sellers list their products, buyers place orders.

Endpoints (all under ``/api/v1``):

Listings
--------
* ``POST   /marketplace/listings``                       — seller creates a listing.
* ``GET    /marketplace/listings``                       — buyers browse with nutrient filters.
* ``GET    /marketplace/listings/{listing_id}``          — single listing detail.
* ``PUT    /marketplace/listings/{listing_id}``          — seller updates their own listing.
* ``DELETE /marketplace/listings/{listing_id}``          — seller removes their own listing.
* ``GET    /marketplace/sellers/{seller_id}/listings``   — listings for a specific seller.

Orders
------
* ``POST  /marketplace/orders``                          — buyer places an order (may split by seller).
* ``GET   /marketplace/orders``                          — list orders for either buyer or seller.
* ``GET   /marketplace/orders/{order_id}``               — order detail.
* ``PATCH /marketplace/orders/{order_id}/status``        — seller (or buyer when cancelling) changes status.
"""

from __future__ import annotations

import json
import os
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import (
    FoodListing,
    Order,
    OrderItem,
    OrderStatusEnum,
    User,
    UserRoleEnum,
)
from schemas.marketplace import (
    FoodListingCreate,
    FoodListingResponse,
    FoodListingUpdate,
    NutritionPayload,
    OrderCreate,
    OrderItemResponse,
    OrderResponse,
    OrderStatusUpdate,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Uploads (listing images)
# ---------------------------------------------------------------------------

# Resolve the uploads directory relative to the backend package root so the
# location is stable regardless of the current working directory the server
# was started from.
UPLOAD_DIR: Path = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_TYPES: Dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB


@router.post("/marketplace/uploads", status_code=201)
async def upload_listing_image(
    request: Request,
    file: UploadFile = File(..., description="Image file to upload (jpeg/png/webp/gif)"),
):
    """Accept a local image upload from the seller dashboard.

    Persists the file under ``backend/uploads/<uuid><ext>`` and returns the
    public URL that will be mounted at ``/uploads`` by :mod:`backend.main`.
    Callers then store the returned URL in ``FoodListing.image_url``.
    """
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{content_type}'. Upload a JPEG, PNG, WEBP or GIF image.",
        )

    ext = ALLOWED_IMAGE_TYPES[content_type]
    # Prefer the real extension if the client provided a sensible one.
    if file.filename:
        _, client_ext = os.path.splitext(file.filename)
        client_ext = client_ext.lower()
        if client_ext in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            ext = ".jpg" if client_ext == ".jpeg" else client_ext

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    filename = f"{uuid.uuid4().hex}{ext}"
    target = UPLOAD_DIR / filename
    with target.open("wb") as fh:
        fh.write(contents)

    # ``request.base_url`` already ends with '/'.
    absolute_url = f"{str(request.base_url).rstrip('/')}/uploads/{filename}"
    return {
        "url": absolute_url,
        "path": f"/uploads/{filename}",
        "filename": filename,
        "size": len(contents),
        "content_type": content_type,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _ensure_seller(user: User) -> None:
    if user.role not in (UserRoleEnum.seller.value, UserRoleEnum.both.value):
        raise HTTPException(
            status_code=403,
            detail="User is not a seller. Promote the account via PATCH /profile/{user_id}/role first.",
        )


def _parse_tags(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
        return [str(t) for t in value] if isinstance(value, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _dump_tags(tags: Optional[List[str]]) -> str:
    return json.dumps([t.strip().lower() for t in (tags or []) if t and t.strip()])


def _listing_to_response(listing: FoodListing) -> FoodListingResponse:
    return FoodListingResponse(
        id=listing.id,
        seller_id=listing.seller_id,
        seller_name=listing.seller.full_name if listing.seller else None,
        name=listing.name,
        description=listing.description,
        image_url=listing.image_url,
        price=listing.price,
        unit=listing.unit,
        stock=listing.stock,
        is_active=listing.is_active,
        serving_size=listing.serving_size,
        calories=listing.calories,
        protein=listing.protein,
        carbs=listing.carbs,
        fat=listing.fat,
        fiber=listing.fiber,
        sugar=listing.sugar,
        sodium=listing.sodium,
        tags=_parse_tags(listing.tags),
        created_at=listing.created_at,
        updated_at=listing.updated_at,
    )


def _nutrition_payload(listing: FoodListing) -> NutritionPayload:
    return NutritionPayload(
        calories=listing.calories,
        protein=listing.protein,
        carbs=listing.carbs,
        fat=listing.fat,
        fiber=listing.fiber,
        sugar=listing.sugar,
        sodium=listing.sodium,
    )


def _order_to_response(order: Order) -> OrderResponse:
    items: List[OrderItemResponse] = []
    for it in order.items:
        listing = it.listing
        items.append(
            OrderItemResponse(
                id=it.id,
                listing_id=it.listing_id,
                name_snapshot=it.name_snapshot,
                unit_price=it.unit_price,
                quantity=it.quantity,
                listing_image_url=listing.image_url if listing else None,
                listing_nutrition=_nutrition_payload(listing) if listing else None,
                listing_tags=_parse_tags(listing.tags) if listing else [],
            )
        )

    nutrient_target: Optional[NutritionPayload] = None
    if order.nutrient_target:
        try:
            nutrient_target = NutritionPayload(**json.loads(order.nutrient_target))
        except (json.JSONDecodeError, TypeError):
            nutrient_target = None

    return OrderResponse(
        id=order.id,
        buyer_id=order.buyer_id,
        seller_id=order.seller_id,
        buyer_name=order.buyer.full_name if order.buyer else None,
        seller_name=order.seller.full_name if order.seller else None,
        status=order.status,
        total_price=order.total_price,
        notes=order.notes,
        nutrient_target=nutrient_target,
        items=items,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


# ---------------------------------------------------------------------------
# Listings — seller CRUD
# ---------------------------------------------------------------------------

@router.post("/marketplace/listings", response_model=FoodListingResponse, status_code=201)
def create_listing(
    payload: FoodListingCreate,
    seller_id: int = Query(..., description="ID of the seller creating the listing"),
    db: Session = Depends(get_db),
):
    seller = _get_user(db, seller_id)
    _ensure_seller(seller)

    listing = FoodListing(
        seller_id=seller.id,
        name=payload.name.strip(),
        description=payload.description,
        image_url=payload.image_url,
        price=payload.price,
        unit=payload.unit,
        stock=payload.stock,
        is_active=True,
        serving_size=payload.serving_size,
        calories=payload.calories,
        protein=payload.protein,
        carbs=payload.carbs,
        fat=payload.fat,
        fiber=payload.fiber,
        sugar=payload.sugar,
        sodium=payload.sodium,
        tags=_dump_tags(payload.tags),
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return _listing_to_response(listing)


@router.get("/marketplace/listings", response_model=List[FoodListingResponse])
def search_listings(
    q: Optional[str] = Query(None, description="Name substring"),
    tags: Optional[str] = Query(
        None,
        description="Comma-separated tags; a listing matches if it has ANY of them.",
    ),
    min_protein: Optional[float] = Query(None, ge=0),
    max_sugar: Optional[float] = Query(None, ge=0),
    min_fiber: Optional[float] = Query(None, ge=0),
    max_calories: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    in_stock_only: bool = Query(True),
    sort_by: str = Query(
        "newest",
        pattern="^(newest|protein_per_dollar|price_asc|price_desc)$",
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Buyer-facing search with nutrient filters.

    All nutrient filters refer to the **per-serving** nutrition stored on the
    listing. For cross-seller ranking we expose ``protein_per_dollar`` which
    helps buyers find the highest-protein listings for a given budget.
    """
    query = db.query(FoodListing).filter(FoodListing.is_active.is_(True))

    if in_stock_only:
        query = query.filter(FoodListing.stock > 0)
    if q:
        query = query.filter(FoodListing.name.ilike(f"%{q.strip()}%"))
    if min_protein is not None:
        query = query.filter(FoodListing.protein >= min_protein)
    if max_sugar is not None:
        query = query.filter((FoodListing.sugar.is_(None)) | (FoodListing.sugar <= max_sugar))
    if min_fiber is not None:
        query = query.filter(FoodListing.fiber >= min_fiber)
    if max_calories is not None:
        query = query.filter(FoodListing.calories <= max_calories)
    if max_price is not None:
        query = query.filter(FoodListing.price <= max_price)

    rows = query.all()

    # Tag filter (JSON-string storage => do it in Python for portability)
    tag_set = {t.strip().lower() for t in tags.split(",") if t.strip()} if tags else set()
    if tag_set:
        rows = [r for r in rows if tag_set & set(_parse_tags(r.tags))]

    # Sort
    if sort_by == "price_asc":
        rows.sort(key=lambda r: r.price)
    elif sort_by == "price_desc":
        rows.sort(key=lambda r: r.price, reverse=True)
    elif sort_by == "protein_per_dollar":
        def ppd(r: FoodListing) -> float:
            if not r.protein or not r.price:
                return -1.0
            return r.protein / r.price
        rows.sort(key=ppd, reverse=True)
    else:  # newest
        rows.sort(key=lambda r: r.created_at or 0, reverse=True)

    rows = rows[offset : offset + limit]
    return [_listing_to_response(r) for r in rows]


@router.get("/marketplace/listings/{listing_id}", response_model=FoodListingResponse)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(FoodListing).filter(FoodListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return _listing_to_response(listing)


@router.put("/marketplace/listings/{listing_id}", response_model=FoodListingResponse)
def update_listing(
    listing_id: int,
    payload: FoodListingUpdate,
    seller_id: int = Query(..., description="ID of the seller making the change"),
    db: Session = Depends(get_db),
):
    listing = db.query(FoodListing).filter(FoodListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.seller_id != seller_id:
        raise HTTPException(status_code=403, detail="You can only edit your own listings")

    data = payload.model_dump(exclude_unset=True)
    if "tags" in data and data["tags"] is not None:
        listing.tags = _dump_tags(data.pop("tags"))
    for field, value in data.items():
        setattr(listing, field, value)

    db.commit()
    db.refresh(listing)
    return _listing_to_response(listing)


@router.delete("/marketplace/listings/{listing_id}")
def delete_listing(
    listing_id: int,
    seller_id: int = Query(..., description="ID of the seller"),
    db: Session = Depends(get_db),
):
    listing = db.query(FoodListing).filter(FoodListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.seller_id != seller_id:
        raise HTTPException(status_code=403, detail="You can only delete your own listings")

    db.delete(listing)
    db.commit()
    return {"success": True, "deleted_id": listing_id}


@router.get(
    "/marketplace/sellers/{seller_id}/listings",
    response_model=List[FoodListingResponse],
)
def list_seller_listings(
    seller_id: int,
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
):
    _get_user(db, seller_id)
    query = db.query(FoodListing).filter(FoodListing.seller_id == seller_id)
    if not include_inactive:
        query = query.filter(FoodListing.is_active.is_(True))
    rows = query.order_by(FoodListing.created_at.desc()).all()
    return [_listing_to_response(r) for r in rows]


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

@router.post("/marketplace/orders", response_model=List[OrderResponse], status_code=201)
def create_order(
    payload: OrderCreate,
    buyer_id: int = Query(..., description="ID of the buyer placing the order"),
    db: Session = Depends(get_db),
):
    """Place an order. Items from multiple sellers are split into one Order per seller."""
    buyer = _get_user(db, buyer_id)

    # Load every referenced listing once.
    listing_ids = list({i.listing_id for i in payload.items})
    listings = (
        db.query(FoodListing).filter(FoodListing.id.in_(listing_ids)).all()
    )
    by_id: Dict[int, FoodListing] = {l.id: l for l in listings}

    missing = [lid for lid in listing_ids if lid not in by_id]
    if missing:
        raise HTTPException(status_code=404, detail=f"Listings not found: {missing}")

    # Validate stock / active / no self-ordering, and group by seller.
    grouped: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for item in payload.items:
        listing = by_id[item.listing_id]
        if not listing.is_active:
            raise HTTPException(status_code=400, detail=f"Listing #{listing.id} is not active")
        if listing.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for '{listing.name}' (requested {item.quantity}, available {listing.stock})",
            )
        if listing.seller_id == buyer.id:
            raise HTTPException(status_code=400, detail="You cannot order your own listings")
        grouped[listing.seller_id].append({"listing": listing, "qty": item.quantity})

    # Create one Order per seller.
    created: List[Order] = []
    nutrient_target_json = (
        json.dumps(payload.nutrient_target.model_dump(exclude_none=True))
        if payload.nutrient_target
        else None
    )

    for seller_id, line_items in grouped.items():
        total = sum(li["listing"].price * li["qty"] for li in line_items)
        order = Order(
            buyer_id=buyer.id,
            seller_id=seller_id,
            status=OrderStatusEnum.pending.value,
            total_price=round(total, 2),
            notes=payload.notes,
            nutrient_target=nutrient_target_json,
        )
        db.add(order)
        db.flush()  # assign id
        for li in line_items:
            listing: FoodListing = li["listing"]
            qty: int = li["qty"]
            db.add(
                OrderItem(
                    order_id=order.id,
                    listing_id=listing.id,
                    quantity=qty,
                    unit_price=listing.price,
                    name_snapshot=listing.name,
                )
            )
            listing.stock = max(0, listing.stock - qty)
        created.append(order)

    db.commit()
    for o in created:
        db.refresh(o)
    return [_order_to_response(o) for o in created]


@router.get("/marketplace/orders", response_model=List[OrderResponse])
def list_orders(
    user_id: int = Query(..., description="ID of the requesting user"),
    role: str = Query("buyer", pattern="^(buyer|seller)$"),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    _get_user(db, user_id)
    query = db.query(Order)
    if role == "buyer":
        query = query.filter(Order.buyer_id == user_id)
    else:
        query = query.filter(Order.seller_id == user_id)
    if status:
        query = query.filter(Order.status == status)
    rows = query.order_by(Order.created_at.desc()).all()
    return [_order_to_response(o) for o in rows]


@router.get("/marketplace/orders/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    user_id: int = Query(..., description="Requesting user (must be buyer or seller)"),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if user_id not in (order.buyer_id, order.seller_id):
        raise HTTPException(status_code=403, detail="Not allowed to view this order")
    return _order_to_response(order)


@router.patch("/marketplace/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    user_id: int = Query(..., description="Requesting user (buyer for cancel, seller otherwise)"),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    new_status = payload.status.value if hasattr(payload.status, "value") else str(payload.status)

    is_buyer = user_id == order.buyer_id
    is_seller = user_id == order.seller_id
    if not (is_buyer or is_seller):
        raise HTTPException(status_code=403, detail="Not allowed to modify this order")

    # Allowed transitions:
    #   buyer  -> cancelled   (only while pending)
    #   seller -> confirmed   (only from pending)
    #   seller -> fulfilled   (only from confirmed)
    #   seller -> cancelled   (only from pending|confirmed)
    current = order.status
    allowed = False
    if new_status == OrderStatusEnum.cancelled.value:
        if is_buyer and current == OrderStatusEnum.pending.value:
            allowed = True
        if is_seller and current in (
            OrderStatusEnum.pending.value,
            OrderStatusEnum.confirmed.value,
        ):
            allowed = True
    elif new_status == OrderStatusEnum.confirmed.value:
        allowed = is_seller and current == OrderStatusEnum.pending.value
    elif new_status == OrderStatusEnum.fulfilled.value:
        allowed = is_seller and current == OrderStatusEnum.confirmed.value

    if not allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition order from '{current}' to '{new_status}' for this user",
        )

    # If cancelling, restore stock.
    if new_status == OrderStatusEnum.cancelled.value and current in (
        OrderStatusEnum.pending.value,
        OrderStatusEnum.confirmed.value,
    ):
        for item in order.items:
            if item.listing is not None:
                item.listing.stock += item.quantity

    order.status = new_status
    db.commit()
    db.refresh(order)
    return _order_to_response(order)
