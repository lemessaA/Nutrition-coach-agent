from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from database.models import GenderEnum, ActivityLevelEnum, GoalEnum


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserProfileCreate(BaseModel):
    age: int
    weight: float  # kg
    height: float  # cm
    gender: GenderEnum
    activity_level: ActivityLevelEnum
    goal: GoalEnum
    dietary_restrictions: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    preferences: Optional[List[str]] = []


class UserProfileUpdate(BaseModel):
    age: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    gender: Optional[GenderEnum] = None
    activity_level: Optional[ActivityLevelEnum] = None
    goal: Optional[GoalEnum] = None
    dietary_restrictions: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    preferences: Optional[List[str]] = None


class UserProfileResponse(BaseModel):
    id: int
    user_id: int
    age: int
    weight: float
    height: float
    gender: GenderEnum
    activity_level: ActivityLevelEnum
    goal: GoalEnum
    dietary_restrictions: List[str]
    allergies: List[str]
    preferences: List[str]
    bmr: Optional[float] = None
    tdee: Optional[float] = None
    target_calories: Optional[float] = None
    target_protein: Optional[float] = None
    target_carbs: Optional[float] = None
    target_fat: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
