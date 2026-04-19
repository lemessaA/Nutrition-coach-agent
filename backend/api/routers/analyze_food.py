import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database.connection import get_db
from database.models import User, UserProfile, FoodAnalysis
from schemas.food_analysis import FoodAnalysisRequest, FoodAnalysisResponse
from agents.food_analyzer_agent import FoodAnalyzerAgent

router = APIRouter()
food_analyzer_agent = FoodAnalyzerAgent()


def _parse_food_items(raw) -> list:
    """Food items are stored as JSON text; normalize for response."""
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return []


@router.post("/analyze-food", response_model=FoodAnalysisResponse)
async def analyze_food(
    request: FoodAnalysisRequest,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Analyze food for nutritional content"""
    try:
        # Get user profile for context
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        # Prepare user context
        user_context = {}
        if profile:
            user_context = {
                "user_profile": {
                    "goal": profile.goal.value,
                    "target_calories": profile.target_calories,
                    "dietary_restrictions": profile.dietary_restrictions or [],
                    "allergies": profile.allergies or []
                }
            }
        
        # Use food analyzer agent
        agent_input = {
            "action": "analyze",
            "food_input": request.food_input,
            "serving_size": request.serving_size,
            "user_context": user_context
        }
        
        result = await food_analyzer_agent.process(agent_input)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Food analysis failed"))
        
        analysis_data = result["analysis"]
        
        # Save analysis to database
        db_analysis = FoodAnalysis(
            user_id=user_id,
            food_input=request.food_input,
            serving_size=request.serving_size,
            calories=analysis_data.get("total_nutrition", {}).get("calories"),
            protein=analysis_data.get("total_nutrition", {}).get("protein"),
            carbs=analysis_data.get("total_nutrition", {}).get("carbs"),
            fat=analysis_data.get("total_nutrition", {}).get("fat"),
            fiber=analysis_data.get("total_nutrition", {}).get("fiber"),
            sugar=analysis_data.get("total_nutrition", {}).get("sugar"),
            sodium=analysis_data.get("total_nutrition", {}).get("sodium"),
            food_items=json.dumps(analysis_data.get("foods_analyzed", []))
        )
        
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)
        
        return FoodAnalysisResponse(
            id=db_analysis.id,
            user_id=db_analysis.user_id,
            food_input=db_analysis.food_input,
            calories=db_analysis.calories,
            protein=db_analysis.protein,
            carbs=db_analysis.carbs,
            fat=db_analysis.fat,
            fiber=db_analysis.fiber,
            sugar=db_analysis.sugar,
            sodium=db_analysis.sodium,
            serving_size=db_analysis.serving_size,
            food_items=analysis_data.get("foods_analyzed", []),
            created_at=db_analysis.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing food: {str(e)}")


@router.post("/analyze-meal")
async def analyze_meal(
    meal_description: str,
    meal_type: str = "general",
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Analyze a complete meal"""
    try:
        # Get user profile if provided
        user_context = {}
        if user_id:
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if profile:
                user_context = {
                    "user_profile": {
                        "goal": profile.goal.value,
                        "target_calories": profile.target_calories
                    }
                }
        
        # Use food analyzer agent for meal analysis
        agent_input = {
            "action": "meal_analysis",
            "meal_description": meal_description,
            "meal_type": meal_type,
            "user_context": user_context
        }
        
        result = await food_analyzer_agent.process(agent_input)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Meal analysis failed"))
        
        analysis = result["analysis"]
        
        # Save to database if user_id provided
        if user_id:
            db_analysis = FoodAnalysis(
                user_id=user_id,
                food_input=meal_description,
                serving_size=f"{meal_type} meal",
                calories=analysis.get("total_nutrition", {}).get("calories"),
                protein=analysis.get("total_nutrition", {}).get("protein"),
                carbs=analysis.get("total_nutrition", {}).get("carbs"),
                fat=analysis.get("total_nutrition", {}).get("fat"),
                fiber=analysis.get("total_nutrition", {}).get("fiber"),
                sugar=analysis.get("total_nutrition", {}).get("sugar"),
                sodium=analysis.get("total_nutrition", {}).get("sodium"),
                food_items=json.dumps(analysis.get("foods_analyzed", []))
            )
            
            db.add(db_analysis)
            db.commit()
            db.refresh(db_analysis)
            
            analysis["saved_analysis_id"] = db_analysis.id
        
        return {
            "success": True,
            "analysis": analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing meal: {str(e)}")


@router.post("/compare-foods")
async def compare_foods(
    foods: List[str],
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Compare nutritional content of multiple foods"""
    try:
        # Get user context if provided
        user_context = {}
        if user_id:
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if profile:
                user_context = {
                    "user_profile": {
                        "goal": profile.goal.value,
                        "target_calories": profile.target_calories
                    }
                }
        
        # Use food analyzer agent for comparison
        agent_input = {
            "action": "compare",
            "foods": foods,
            "user_context": user_context
        }
        
        result = await food_analyzer_agent.process(agent_input)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Food comparison failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing foods: {str(e)}")


@router.get("/analyze-food/{user_id}/history")
async def get_food_analysis_history(
    user_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get food analysis history for a user"""
    try:
        analyses = db.query(FoodAnalysis).filter(
            FoodAnalysis.user_id == user_id
        ).order_by(FoodAnalysis.created_at.desc()).limit(limit).all()
        
        return [
            FoodAnalysisResponse(
                id=analysis.id,
                user_id=analysis.user_id,
                food_input=analysis.food_input,
                calories=analysis.calories,
                protein=analysis.protein,
                carbs=analysis.carbs,
                fat=analysis.fat,
                fiber=analysis.fiber,
                sugar=analysis.sugar,
                sodium=analysis.sodium,
                serving_size=analysis.serving_size,
                food_items=_parse_food_items(analysis.food_items),
                created_at=analysis.created_at
            )
            for analysis in analyses
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analysis history: {str(e)}")


@router.get("/analyze-food/{analysis_id}", response_model=FoodAnalysisResponse)
async def get_food_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Get a specific food analysis"""
    try:
        analysis = db.query(FoodAnalysis).filter(FoodAnalysis.id == analysis_id).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Food analysis not found")
        
        return FoodAnalysisResponse(
            id=analysis.id,
            user_id=analysis.user_id,
            food_input=analysis.food_input,
            calories=analysis.calories,
            protein=analysis.protein,
            carbs=analysis.carbs,
            fat=analysis.fat,
            fiber=analysis.fiber,
            sugar=analysis.sugar,
            sodium=analysis.sodium,
            serving_size=analysis.serving_size,
            food_items=_parse_food_items(analysis.food_items),
            created_at=analysis.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching food analysis: {str(e)}")


@router.delete("/analyze-food/{analysis_id}")
async def delete_food_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Delete a food analysis"""
    try:
        analysis = db.query(FoodAnalysis).filter(FoodAnalysis.id == analysis_id).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Food analysis not found")
        
        db.delete(analysis)
        db.commit()
        
        return {"message": "Food analysis deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting food analysis: {str(e)}")


@router.get("/analyze-food/{user_id}/summary")
async def get_nutrition_summary(user_id: int, db: Session = Depends(get_db)):
    """Get nutrition summary for a user"""
    try:
        # Get recent analyses
        recent_analyses = db.query(FoodAnalysis).filter(
            FoodAnalysis.user_id == user_id
        ).order_by(FoodAnalysis.created_at.desc()).limit(7).all()  # Last 7 analyses
        
        if not recent_analyses:
            return {"message": "No food analyses found"}
        
        # Calculate averages
        total_calories = sum(a.calories or 0 for a in recent_analyses)
        total_protein = sum(a.protein or 0 for a in recent_analyses)
        total_carbs = sum(a.carbs or 0 for a in recent_analyses)
        total_fat = sum(a.fat or 0 for a in recent_analyses)
        
        count = len(recent_analyses)
        
        summary = {
            "period": "Last 7 analyses",
            "average_per_analysis": {
                "calories": round(total_calories / count, 1),
                "protein": round(total_protein / count, 1),
                "carbs": round(total_carbs / count, 1),
                "fat": round(total_fat / count, 1)
            },
            "total_values": {
                "calories": total_calories,
                "protein": total_protein,
                "carbs": total_carbs,
                "fat": total_fat
            },
            "analysis_count": count,
            "most_recent_analysis": {
                "food_input": recent_analyses[0].food_input,
                "calories": recent_analyses[0].calories,
                "date": recent_analyses[0].created_at
            }
        }
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating nutrition summary: {str(e)}")
