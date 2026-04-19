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


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False) # one-to-one relationship
    meal_plans = relationship("MealPlan", back_populates="user") # one-to-many relationship
    chat_messages = relationship("ChatMessage", back_populates="user") # one-to-many relationship
    food_analyses = relationship("FoodAnalysis", back_populates="user") # one-to-many relationship


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