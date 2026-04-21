from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from database.connection import Base

# pyEnum creation of collection name/values pairs
class GenderEnum(PyEnum):
    male = "male"
    female = "female"
    other = "other"


class ActivityLevelEnum(PyEnum):
    sedentary = "sedentary"
    lightly_active = "lightly_active"
    moderately_active = "moderately_active"
    very_active = "very_active"
    extra_active = "extra_active"


class GoalEnum(PyEnum):
    lose_weight = "lose_weight"
    gain_muscle = "gain_muscle"
    maintain_health = "maintain_health"


class UserRoleEnum(PyEnum):
    buyer = "buyer"
    seller = "seller"
    both = "both"


class OrderStatusEnum(PyEnum):
    pending = "pending"
    confirmed = "confirmed"
    fulfilled = "fulfilled"
    cancelled = "cancelled"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    # Plain string to keep lightweight migrations portable across SQLite / Postgres.
    role = Column(String, nullable=False, default=UserRoleEnum.buyer.value, server_default=UserRoleEnum.buyer.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False) # one-to-one relationship
    meal_plans = relationship("MealPlan", back_populates="user") # one-to-many relationship
    chat_messages = relationship("ChatMessage", back_populates="user") # one-to-many relationship
    food_analyses = relationship("FoodAnalysis", back_populates="user") # one-to-many relationship
    listings = relationship("FoodListing", back_populates="seller", cascade="all, delete-orphan")
    orders_as_buyer = relationship(
        "Order",
        back_populates="buyer",
        foreign_keys="Order.buyer_id",
        cascade="all, delete-orphan",
    )
    orders_as_seller = relationship(
        "Order",
        back_populates="seller",
        foreign_keys="Order.seller_id",
        cascade="all, delete-orphan",
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Physical characteristics
    age = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)  # in kg
    height = Column(Float, nullable=False)  # in cm
    gender = Column(Enum(GenderEnum), nullable=False)
    
    # Lifestyle and goals
    activity_level = Column(Enum(ActivityLevelEnum), nullable=False)
    goal = Column(Enum(GoalEnum), nullable=False)
    
    # Dietary preferences and restrictions
    dietary_restrictions = Column(Text)  # JSON string
    allergies = Column(Text)  # JSON string
    preferences = Column(Text)  # JSON string
    
    # Calculated values
    bmr = Column(Float)  # Basal Metabolic Rate
    tdee = Column(Float)  # Total Daily Energy Expenditure
    target_calories = Column(Float)
    target_protein = Column(Float)  # in grams
    target_carbs = Column(Float)  # in grams
    target_fat = Column(Float)  # in grams
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="profile") # many-to-one relationship that means many user profiles can belong to one user


class MealPlan(Base):
    __tablename__ = "meal_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Plan details
    plan_type = Column(String, nullable=False)  # daily, weekly
    plan_date = Column(DateTime(timezone=True), nullable=False)
    meals = Column(Text, nullable=False)  # JSON string with meal details
    
    # Nutrition summary
    total_calories = Column(Float)
    total_protein = Column(Float)
    total_carbs = Column(Float)
    total_fat = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="meal_plans") # many-to-one relationship that means many meal plans can belong to one user


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    agent_type = Column(String, nullable=False)  # profile, meal_planner, nutrition, food_analyzer, coach
    session_id = Column(String, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_messages") # many-to-one relationship that means many chat messages can belong to one user


class FoodAnalysis(Base):
    __tablename__ = "food_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    food_input = Column(Text, nullable=False)
    
    # Analysis results
    calories = Column(Float)
    protein = Column(Float)
    carbs = Column(Float)
    fat = Column(Float)
    fiber = Column(Float)
    sugar = Column(Float)
    sodium = Column(Float)
    
    # Additional details
    serving_size = Column(String)
    food_items = Column(Text)  # JSON string of individual food items
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="food_analyses") # many-to-one relationship that means many food analyses can belong to one user


class NutritionKnowledge(Base):
    __tablename__ = "nutrition_knowledge"
    
    id = Column(Integer, primary_key=True, index=True)
    
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String, nullable=False)  # protein, carbs, fats, vitamins, minerals, etc.
    source = Column(String)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class MarketData(Base):
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    
    food_item = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    unit = Column(String, nullable=False)  # per kg, per lb, per item
    location = Column(String)
    source = Column(String)  # supermarket, farmers_market, etc.
    
    # Availability
    in_stock = Column(Boolean, default=True)
    seasonal = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ---------------------------------------------------------------------------
# Marketplace (food seller / buyer e-commerce)
# ---------------------------------------------------------------------------

class FoodListing(Base):
    """A food product that a seller offers on the marketplace."""

    __tablename__ = "food_listings"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Product details
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    image_url = Column(String)

    # Pricing and availability
    price = Column(Float, nullable=False)           # price per serving/unit
    unit = Column(String, nullable=False, default="serving")  # e.g. "serving", "kg", "bag"
    stock = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)

    # Nutrition (per serving/unit)
    serving_size = Column(String)           # human-readable e.g. "100 g"
    calories = Column(Float)
    protein = Column(Float)
    carbs = Column(Float)
    fat = Column(Float)
    fiber = Column(Float)
    sugar = Column(Float)
    sodium = Column(Float)

    # Freeform tags: "vegan", "gluten-free", "high-protein", "organic" ...
    tags = Column(Text)  # JSON array string

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    seller = relationship("User", back_populates="listings")
    order_items = relationship("OrderItem", back_populates="listing")


class Order(Base):
    """A buyer's order with one seller.

    Orders are per-seller: if a buyer places items from multiple sellers the
    API splits the cart into separate ``Order`` rows so each seller can manage
    their own fulfilment independently.
    """

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    status = Column(
        String,
        nullable=False,
        default=OrderStatusEnum.pending.value,
        server_default=OrderStatusEnum.pending.value,
    )
    total_price = Column(Float, nullable=False, default=0.0)
    # Optional buyer-supplied nutrition targets for this order.
    nutrient_target = Column(Text)  # JSON string
    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    buyer = relationship("User", back_populates="orders_as_buyer", foreign_keys=[buyer_id])
    seller = relationship("User", back_populates="orders_as_seller", foreign_keys=[seller_id])
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    """A single line-item on an order referencing a listing."""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    listing_id = Column(Integer, ForeignKey("food_listings.id"), nullable=False, index=True)

    quantity = Column(Integer, nullable=False, default=1)
    # Snapshot of the listing at order time so history stays correct even if
    # the seller later renames or reprices their product.
    unit_price = Column(Float, nullable=False)
    name_snapshot = Column(String, nullable=False)

    order = relationship("Order", back_populates="items")
    listing = relationship("FoodListing", back_populates="order_items")