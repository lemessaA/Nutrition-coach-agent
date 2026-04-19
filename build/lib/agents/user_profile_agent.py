from typing import Dict, Any, List
import json
from agents.base import BaseAgent
from database.models import UserProfile
from database.models import GenderEnum, ActivityLevelEnum, GoalEnum


class UserProfileAgent(BaseAgent):
    """Agent for managing user health profiles and calculating nutritional targets"""
    
    def __init__(self):
        super().__init__("User Profile Agent")
    
    def get_system_prompt(self) -> str:
        return """You are a nutrition and health expert specializing in creating personalized user profiles.
        Your role is to:
        1. Collect and validate user health information
        2. Calculate Basal Metabolic Rate (BMR) and Total Daily Energy Expenditure (TDEE)
        3. Determine personalized macro targets based on user goals
        4. Provide recommendations for healthy eating patterns
        
        Always be encouraging, professional, and evidence-based in your responses.
        If information is missing, ask specific questions to gather the necessary details."""
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user profile requests"""
        action = input_data.get("action", "create")
        
        if action == "create":
            return await self.create_profile(input_data)
        elif action == "update":
            return await self.update_profile(input_data)
        elif action == "calculate_targets":
            return await self.calculate_nutritional_targets(input_data)
        elif action == "validate_profile":
            return await self.validate_profile(input_data)
        else:
            return {"error": f"Unknown action: {action}"}
    
    async def create_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user profile with calculated targets"""
        try:
            # Validate required fields
            required_fields = ["age", "weight", "height", "gender", "activity_level", "goal"]
            missing_fields = [field for field in required_fields if field not in profile_data]
            
            if missing_fields:
                return {
                    "error": f"Missing required fields: {', '.join(missing_fields)}",
                    "suggestions": await self.get_profile_questions(missing_fields)
                }
            
            # Calculate nutritional targets
            targets = await self.calculate_nutritional_targets(profile_data)
            
            if "error" in targets:
                return targets
            
            # Merge targets with profile data
            profile_data.update(targets)
            
            return {
                "success": True,
                "profile": profile_data,
                "message": "Profile created successfully with personalized nutritional targets",
                "recommendations": await self.get_initial_recommendations(profile_data)
            }
            
        except Exception as e:
            return {"error": f"Error creating profile: {str(e)}"}
    
    async def update_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing user profile"""
        try:
            # Recalculate targets if relevant fields changed
            target_fields = ["weight", "height", "age", "gender", "activity_level", "goal"]
            needs_recalculation = any(field in profile_data for field in target_fields)
            
            if needs_recalculation:
                targets = await self.calculate_nutritional_targets(profile_data)
                if "error" not in targets:
                    profile_data.update(targets)
            
            return {
                "success": True,
                "profile": profile_data,
                "message": "Profile updated successfully",
                "targets_updated": needs_recalculation
            }
            
        except Exception as e:
            return {"error": f"Error updating profile: {str(e)}"}
    
    async def calculate_nutritional_targets(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate BMR, TDEE, and macro targets"""
        try:
            age = float(profile_data["age"])
            weight = float(profile_data["weight"])  # kg
            height = float(profile_data["height"])  # cm
            gender = profile_data["gender"]
            activity_level = profile_data["activity_level"]
            goal = profile_data["goal"]
            
            # Calculate BMR using Mifflin-St Jeor Equation
            if gender == GenderEnum.male:
                bmr = 10 * weight + 6.25 * height - 5 * age + 5
            else:
                bmr = 10 * weight + 6.25 * height - 5 * age - 161
            
            # Activity multipliers
            activity_multipliers = {
                ActivityLevelEnum.sedentary: 1.2,
                ActivityLevelEnum.lightly_active: 1.375,
                ActivityLevelEnum.moderately_active: 1.55,
                ActivityLevelEnum.very_active: 1.725,
                ActivityLevelEnum.extra_active: 1.9
            }
            
            tdee = bmr * activity_multipliers.get(activity_level, 1.2)
            
            # Adjust calories based on goal
            if goal == GoalEnum.lose_weight:
                target_calories = tdee * 0.8  # 20% deficit
            elif goal == GoalEnum.gain_muscle:
                target_calories = tdee * 1.1  # 10% surplus
            else:  # maintain_health
                target_calories = tdee
            
            # Calculate macro targets (protein-focused approach)
            if goal == GoalEnum.gain_muscle:
                protein_per_kg = 2.2  # higher protein for muscle gain
            else:
                protein_per_kg = 1.6  # standard protein recommendation
            
            target_protein = weight * protein_per_kg
            protein_calories = target_protein * 4
            
            # Fat: 20-30% of total calories
            target_fat = (target_calories * 0.25) / 9
            
            # Carbs: remaining calories
            carb_calories = target_calories - protein_calories - (target_fat * 9)
            target_carbs = carb_calories / 4
            
            return {
                "bmr": round(bmr, 0),
                "tdee": round(tdee, 0),
                "target_calories": round(target_calories, 0),
                "target_protein": round(target_protein, 0),
                "target_carbs": round(target_carbs, 0),
                "target_fat": round(target_fat, 0)
            }
            
        except Exception as e:
            return {"error": f"Error calculating nutritional targets: {str(e)}"}
    
    async def validate_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate profile data and provide feedback"""
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Age validation
        if "age" in profile_data:
            age = profile_data["age"]
            if age < 16 or age > 100:
                validation_results["errors"].append("Age should be between 16 and 100")
                validation_results["valid"] = False
            elif age < 18:
                validation_results["warnings"].append("Users under 18 should consult with a healthcare provider")
        
        # Weight validation
        if "weight" in profile_data:
            weight = profile_data["weight"]
            if weight < 30 or weight > 300:
                validation_results["errors"].append("Weight should be between 30kg and 300kg")
                validation_results["valid"] = False
        
        # Height validation
        if "height" in profile_data:
            height = profile_data["height"]
            if height < 100 or height > 250:
                validation_results["errors"].append("Height should be between 100cm and 250cm")
                validation_results["valid"] = False
        
        # BMI calculation and warning
        if "weight" in profile_data and "height" in profile_data:
            bmi = profile_data["weight"] / ((profile_data["height"] / 100) ** 2)
            if bmi < 18.5:
                validation_results["warnings"].append("BMI indicates underweight - consider consulting a healthcare provider")
            elif bmi > 30:
                validation_results["warnings"].append("BMI indicates obesity - consider consulting a healthcare provider")
        
        return validation_results
    
    async def get_profile_questions(self, missing_fields: List[str]) -> List[str]:
        """Generate questions to collect missing profile information"""
        questions = []
        
        field_questions = {
            "age": "What is your age?",
            "weight": "What is your current weight in kilograms?",
            "height": "What is your height in centimeters?",
            "gender": "What is your gender? (male, female, or other)",
            "activity_level": "How would you describe your activity level? (sedentary, lightly_active, moderately_active, very_active, extra_active)",
            "goal": "What is your primary nutrition goal? (lose_weight, gain_muscle, maintain_health)"
        }
        
        for field in missing_fields:
            if field in field_questions:
                questions.append(field_questions[field])
        
        return questions
    
    async def get_initial_recommendations(self, profile_data: Dict[str, Any]) -> List[str]:
        """Generate initial recommendations based on profile"""
        prompt = f"""
        Based on the following user profile, provide 3-5 personalized nutrition recommendations:
        
        Age: {profile_data.get('age')}
        Weight: {profile_data.get('weight')}kg
        Height: {profile_data.get('height')}cm
        Gender: {profile_data.get('gender')}
        Activity Level: {profile_data.get('activity_level')}
        Goal: {profile_data.get('goal')}
        Target Calories: {profile_data.get('target_calories')}
        
        Provide specific, actionable recommendations that align with their goals.
        """
        
        response = await self.generate_response(prompt)
        # Parse response into list of recommendations
        recommendations = [rec.strip() for rec in response.split('\n') if rec.strip()]
        return recommendations[:5]  # Limit to 5 recommendations
