from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import json
from typing import Optional, List

from database.connection import get_db
from database.models import User, UserProfile
from schemas.user import UserCreate, UserResponse, UserProfileCreate, UserProfileUpdate, UserProfileResponse
from agents.user_profile_agent import UserProfileAgent

router = APIRouter()
profile_agent = UserProfileAgent()


def parse_json_field(field: str) -> List[str]:
    """Parse JSON string field to list, return empty list if invalid"""
    if not field or field == "[]":
        return []
    try:
        parsed = json.loads(field)
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


@router.post("/profile", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    try:
        normalized_email = user.email.strip().lower() if user.email else user.email
        existing_user = db.query(User).filter(User.email == normalized_email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        db_user = User(
            email=normalized_email,
            full_name=user.full_name
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return UserResponse(
            id=db_user.id,
            email=db_user.email,
            full_name=db_user.full_name,
            created_at=db_user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")


@router.get("/profile/by-email", response_model=UserResponse)
async def get_user_by_email(
    email: str = Query(..., description="Email address of the user"),
    db: Session = Depends(get_db),
):
    """Look up a user by email (used for lightweight email-based sign-in)."""
    try:
        normalized = email.strip().lower()
        user = db.query(User).filter(User.email == normalized).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")


@router.get("/profile/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user information"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")


@router.post("/profile/{user_id}/health", response_model=UserProfileResponse)
async def create_user_profile(
    user_id: int,
    profile: UserProfileCreate,
    db: Session = Depends(get_db)
):
    """Create or update user health profile"""
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if profile already exists
        existing_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if existing_profile:
            raise HTTPException(status_code=400, detail="Profile already exists. Use PUT to update.")
        
        # Use profile agent to calculate targets and validate
        profile_data = profile.dict()
        agent_result = await profile_agent.create_profile(profile_data)
        
        if not agent_result.get("success"):
            raise HTTPException(status_code=400, detail=agent_result.get("error", "Profile creation failed"))
        
        # Create profile with calculated targets
        calculated_profile = agent_result["profile"]
        import json
        
        db_profile = UserProfile(
            user_id=user_id,
            age=calculated_profile["age"],
            weight=calculated_profile["weight"],
            height=calculated_profile["height"],
            gender=calculated_profile["gender"],
            activity_level=calculated_profile["activity_level"],
            goal=calculated_profile["goal"],
            dietary_restrictions=json.dumps(calculated_profile.get("dietary_restrictions", [])),
            allergies=json.dumps(calculated_profile.get("allergies", [])),
            preferences=json.dumps(calculated_profile.get("preferences", [])),
            bmr=calculated_profile.get("bmr"),
            tdee=calculated_profile.get("tdee"),
            target_calories=calculated_profile.get("target_calories"),
            target_protein=calculated_profile.get("target_protein"),
            target_carbs=calculated_profile.get("target_carbs"),
            target_fat=calculated_profile.get("target_fat")
        )
        
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        
        return UserProfileResponse(
            id=db_profile.id,
            user_id=db_profile.user_id,
            age=db_profile.age,
            weight=db_profile.weight,
            height=db_profile.height,
            gender=db_profile.gender,
            activity_level=db_profile.activity_level,
            goal=db_profile.goal,
            dietary_restrictions=json.loads(db_profile.dietary_restrictions) if db_profile.dietary_restrictions else [],
            allergies=json.loads(db_profile.allergies) if db_profile.allergies else [],
            preferences=json.loads(db_profile.preferences) if db_profile.preferences else [],
            bmr=db_profile.bmr,
            tdee=db_profile.tdee,
            target_calories=db_profile.target_calories,
            target_protein=db_profile.target_protein,
            target_carbs=db_profile.target_carbs,
            target_fat=db_profile.target_fat,
            created_at=db_profile.created_at,
            updated_at=db_profile.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating profile: {str(e)}")


@router.put("/profile/{user_id}/health", response_model=UserProfileResponse)
async def update_user_profile(
    user_id: int,
    profile: UserProfileUpdate,
    db: Session = Depends(get_db)
):
    """Update user health profile"""
    try:
        # Get existing profile
        db_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not db_profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Update fields
        update_data = profile.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_profile, field, value)
        
        # Recalculate targets if relevant fields changed
        target_fields = ["age", "weight", "height", "gender", "activity_level", "goal"]
        needs_recalculation = any(field in update_data for field in target_fields)
        
        if needs_recalculation:
            profile_data = {
                "age": db_profile.age,
                "weight": db_profile.weight,
                "height": db_profile.height,
                "gender": db_profile.gender,
                "activity_level": db_profile.activity_level,
                "goal": db_profile.goal
            }
            
            agent_result = await profile_agent.calculate_nutritional_targets(profile_data)
            if agent_result.get("success"):
                db_profile.bmr = agent_result.get("bmr")
                db_profile.tdee = agent_result.get("tdee")
                db_profile.target_calories = agent_result.get("target_calories")
                db_profile.target_protein = agent_result.get("target_protein")
                db_profile.target_carbs = agent_result.get("target_carbs")
                db_profile.target_fat = agent_result.get("target_fat")
        
        db.commit()
        db.refresh(db_profile)
        
        return UserProfileResponse(
            id=db_profile.id,
            user_id=db_profile.user_id,
            age=db_profile.age,
            weight=db_profile.weight,
            height=db_profile.height,
            gender=db_profile.gender,
            activity_level=db_profile.activity_level,
            goal=db_profile.goal,
            dietary_restrictions=parse_json_field(db_profile.dietary_restrictions),
            allergies=parse_json_field(db_profile.allergies),
            preferences=parse_json_field(db_profile.preferences),
            bmr=db_profile.bmr,
            tdee=db_profile.tdee,
            target_calories=db_profile.target_calories,
            target_protein=db_profile.target_protein,
            target_carbs=db_profile.target_carbs,
            target_fat=db_profile.target_fat,
            created_at=db_profile.created_at,
            updated_at=db_profile.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating profile: {str(e)}")


@router.get("/profile/{user_id}/health", response_model=UserProfileResponse)
async def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """Get user health profile"""
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return UserProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            age=profile.age,
            weight=profile.weight,
            height=profile.height,
            gender=profile.gender,
            activity_level=profile.activity_level,
            goal=profile.goal,
            dietary_restrictions=parse_json_field(profile.dietary_restrictions),
            allergies=parse_json_field(profile.allergies),
            preferences=parse_json_field(profile.preferences),
            bmr=profile.bmr,
            tdee=profile.tdee,
            target_calories=profile.target_calories,
            target_protein=profile.target_protein,
            target_carbs=profile.target_carbs,
            target_fat=profile.target_fat,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching profile: {str(e)}")


@router.delete("/profile/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete user and all related data"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        db.delete(user)
        db.commit()
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")


@router.get("/profile/{user_id}/summary")
async def get_profile_summary(user_id: int, db: Session = Depends(get_db)):
    """Get user profile summary with insights"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        summary = {
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "created_at": user.created_at
            }
        }
        
        if profile:
            summary["health_profile"] = {
                "age": profile.age,
                "weight": profile.weight,
                "height": profile.height,
                "gender": profile.gender.value,
                "activity_level": profile.activity_level.value,
                "goal": profile.goal.value,
                "target_calories": profile.target_calories,
                "target_protein": profile.target_protein,
                "target_carbs": profile.target_carbs,
                "target_fat": profile.target_fat,
                "bmr": profile.bmr,
                "tdee": profile.tdee
            }
            
            # Calculate BMI
            if profile.weight and profile.height:
                bmi = profile.weight / ((profile.height / 100) ** 2)
                summary["health_profile"]["bmi"] = round(bmi, 1)
                
                # BMI category
                if bmi < 18.5:
                    bmi_category = "Underweight"
                elif bmi < 25:
                    bmi_category = "Normal weight"
                elif bmi < 30:
                    bmi_category = "Overweight"
                else:
                    bmi_category = "Obese"
                summary["health_profile"]["bmi_category"] = bmi_category
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching profile summary: {str(e)}")
