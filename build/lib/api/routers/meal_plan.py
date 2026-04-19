from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database.connection import get_db
from database.models import User, UserProfile, MealPlan
from schemas.meal_plan import MealPlanCreate, MealPlanResponse
from agents.meal_planner_agent import MealPlannerAgent

router = APIRouter()
meal_planner_agent = MealPlannerAgent()


@router.post("/meal-plan", response_model=MealPlanResponse)
async def create_meal_plan(
    request: MealPlanCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Create a personalized meal plan"""
    try:
        # Get user profile
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            raise HTTPException(status_code=400, detail="User profile not found. Create profile first.")
        
        # Prepare user profile data for agent
        user_profile_data = {
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
            "dietary_restrictions": profile.dietary_restrictions or [],
            "allergies": profile.allergies or [],
            "preferences": profile.preferences or []
        }
        
        # Use meal planner agent
        agent_input = {
            "action": "generate",
            "plan_type": request.plan_type,
            "user_profile": user_profile_data,
            "preferences": request.preferences or {}
        }
        
        result = await meal_planner_agent.process(agent_input)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Meal plan generation failed"))
        
        meal_plan_data = result["meal_plan"]
        
        # Save meal plan to database
        import json
        
        db_meal_plan = MealPlan(
            user_id=user_id,
            plan_type=request.plan_type,
            plan_date=request.plan_date or datetime.now(),
            meals=json.dumps(meal_plan_data),
            total_calories=meal_plan_data.get("daily_totals", {}).get("calories"),
            total_protein=meal_plan_data.get("daily_totals", {}).get("protein"),
            total_carbs=meal_plan_data.get("daily_totals", {}).get("carbs"),
            total_fat=meal_plan_data.get("daily_totals", {}).get("fat")
        )
        
        db.add(db_meal_plan)
        db.commit()
        db.refresh(db_meal_plan)
        
        return MealPlanResponse(
            id=db_meal_plan.id,
            user_id=db_meal_plan.user_id,
            plan_type=db_meal_plan.plan_type,
            plan_date=db_meal_plan.plan_date,
            meals=json.loads(db_meal_plan.meals) if db_meal_plan.meals else {},
            total_calories=db_meal_plan.total_calories,
            total_protein=db_meal_plan.total_protein,
            total_carbs=db_meal_plan.total_carbs,
            total_fat=db_meal_plan.total_fat,
            created_at=db_meal_plan.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating meal plan: {str(e)}")


@router.get("/meal-plan/{user_id}", response_model=List[MealPlanResponse])
async def get_meal_plans(
    user_id: int,
    plan_type: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get meal plans for a user"""
    try:
        query = db.query(MealPlan).filter(MealPlan.user_id == user_id)
        
        if plan_type:
            query = query.filter(MealPlan.plan_type == plan_type)
        
        meal_plans = query.order_by(MealPlan.created_at.desc()).limit(limit).all()
        
        return [
            MealPlanResponse(
                id=plan.id,
                user_id=plan.user_id,
                plan_type=plan.plan_type,
                plan_date=plan.plan_date,
                meals=plan.meals,
                total_calories=plan.total_calories,
                total_protein=plan.total_protein,
                total_carbs=plan.total_carbs,
                total_fat=plan.total_fat,
                created_at=plan.created_at
            )
            for plan in meal_plans
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching meal plans: {str(e)}")


@router.get("/meal-plan/{plan_id}", response_model=MealPlanResponse)
async def get_meal_plan(plan_id: int, db: Session = Depends(get_db)):
    """Get a specific meal plan"""
    try:
        meal_plan = db.query(MealPlan).filter(MealPlan.id == plan_id).first()
        if not meal_plan:
            raise HTTPException(status_code=404, detail="Meal plan not found")
        
        return MealPlanResponse(
            id=meal_plan.id,
            user_id=meal_plan.user_id,
            plan_type=meal_plan.plan_type,
            plan_date=meal_plan.plan_date,
            meals=meal_plan.meals,
            total_calories=meal_plan.total_calories,
            total_protein=meal_plan.total_protein,
            total_carbs=meal_plan.total_carbs,
            total_fat=meal_plan.total_fat,
            created_at=meal_plan.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching meal plan: {str(e)}")


@router.delete("/meal-plan/{plan_id}")
async def delete_meal_plan(plan_id: int, db: Session = Depends(get_db)):
    """Delete a meal plan"""
    try:
        meal_plan = db.query(MealPlan).filter(MealPlan.id == plan_id).first()
        if not meal_plan:
            raise HTTPException(status_code=404, detail="Meal plan not found")
        
        db.delete(meal_plan)
        db.commit()
        
        return {"message": "Meal plan deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting meal plan: {str(e)}")


@router.get("/meal-plan/{user_id}/suggestions")
async def get_meal_suggestions(
    user_id: int,
    meal_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get meal suggestions based on user profile"""
    try:
        # Get user profile
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Prepare user profile data
        user_profile_data = {
            "age": profile.age,
            "weight": profile.weight,
            "height": profile.height,
            "gender": profile.gender.value,
            "activity_level": profile.activity_level.value,
            "goal": profile.goal.value,
            "dietary_restrictions": profile.dietary_restrictions or [],
            "allergies": profile.allergies or [],
            "preferences": profile.preferences or []
        }
        
        # Get meal suggestions
        agent_input = {
            "action": "meal_suggestions",
            "meal_type": meal_type or "any",
            "user_profile": user_profile_data
        }
        
        result = await meal_planner_agent.process(agent_input)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get suggestions"))
        
        return {
            "meal_type": meal_type or "any",
            "suggestions": result.get("suggestions", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting meal suggestions: {str(e)}")


@router.post("/meal-plan/{user_id}/generate-weekly")
async def generate_weekly_meal_plan(
    user_id: int,
    preferences: Optional[dict] = None,
    db: Session = Depends(get_db)
):
    """Generate a weekly meal plan"""
    try:
        # Get user profile
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Prepare user profile data
        user_profile_data = {
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
            "dietary_restrictions": profile.dietary_restrictions or [],
            "allergies": profile.allergies or [],
            "preferences": profile.preferences or []
        }
        
        # Generate weekly plan
        agent_input = {
            "action": "weekly",
            "user_profile": user_profile_data,
            "preferences": preferences or {}
        }
        
        result = await meal_planner_agent.process(agent_input)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Weekly meal plan generation failed"))
        
        weekly_plan = result["meal_plan"]
        
        # Save each day's meal plan
        saved_plans = []
        for day_name, day_plan in weekly_plan.items():
            if day_name != "shopping_list":  # Skip shopping list for now
                db_meal_plan = MealPlan(
                    user_id=user_id,
                    plan_type="weekly",
                    plan_date=datetime.now(),  # Would be adjusted for actual day
                    meals=day_plan,
                    total_calories=day_plan.get("daily_totals", {}).get("calories"),
                    total_protein=day_plan.get("daily_totals", {}).get("protein"),
                    total_carbs=day_plan.get("daily_totals", {}).get("carbs"),
                    total_fat=day_plan.get("daily_totals", {}).get("fat")
                )
                
                db.add(db_meal_plan)
                saved_plans.append(db_meal_plan)
        
        db.commit()
        
        # Refresh all saved plans
        for plan in saved_plans:
            db.refresh(plan)
        
        return {
            "success": True,
            "weekly_plan": weekly_plan,
            "shopping_list": result.get("shopping_list", []),
            "plans_saved": len(saved_plans)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating weekly meal plan: {str(e)}")
