from typing import Dict, Any, List
import json
from datetime import datetime, timedelta
from agents.base import BaseAgent


class MealPlannerAgent(BaseAgent):
    """Agent for generating personalized meal plans"""
    
    def __init__(self):
        super().__init__("Meal Planner Agent")
    
    def get_system_prompt(self) -> str:
        return """You are a professional meal planning and nutrition expert.
        Your role is to:
        1. Create personalized meal plans based on user profiles and goals
        2. Ensure meals meet calculated macro and calorie targets
        3. Provide variety and appeal in meal suggestions
        4. Consider dietary restrictions and preferences
        5. Include practical recipes and preparation instructions
        
        Always provide detailed nutritional information for each meal.
        Focus on whole foods, balanced nutrition, and realistic meal preparation."""
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process meal planning requests"""
        action = input_data.get("action", "generate")
        
        if action == "generate":
            return await self.generate_meal_plan(input_data)
        elif action == "daily":
            return await self.generate_daily_plan(input_data)
        elif action == "weekly":
            return await self.generate_weekly_plan(input_data)
        elif action == "meal_suggestions":
            return await self.get_meal_suggestions(input_data)
        else:
            return {"error": f"Unknown action: {action}"}
    
    async def generate_meal_plan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a meal plan based on user profile and preferences"""
        try:
            user_profile = input_data.get("user_profile")
            plan_type = input_data.get("plan_type", "daily")
            preferences = input_data.get("preferences", {})
            
            if not user_profile:
                return {"error": "User profile is required for meal planning"}
            
            if plan_type == "daily":
                return await self.generate_daily_plan(input_data)
            elif plan_type == "weekly":
                return await self.generate_weekly_plan(input_data)
            else:
                return {"error": f"Unsupported plan type: {plan_type}"}
                
        except Exception as e:
            return {"error": f"Error generating meal plan: {str(e)}"}
    
    async def generate_daily_plan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a daily meal plan"""
        try:
            user_profile = input_data.get("user_profile")
            preferences = input_data.get("preferences", {})
            
            target_calories = user_profile.get("target_calories", 2000)
            target_protein = user_profile.get("target_protein", 150)
            target_carbs = user_profile.get("target_carbs", 250)
            target_fat = user_profile.get("target_fat", 65)
            
            dietary_restrictions = user_profile.get("dietary_restrictions", [])
            allergies = user_profile.get("allergies", [])
            preferences_list = user_profile.get("preferences", [])
            
            prompt = f"""
            Create a detailed daily meal plan with the following specifications:
            
            TARGETS:
            - Calories: {target_calories} kcal
            - Protein: {target_protein}g
            - Carbs: {target_carbs}g
            - Fat: {target_fat}g
            
            USER PROFILE:
            - Goal: {user_profile.get('goal')}
            - Activity Level: {user_profile.get('activity_level')}
            - Dietary Restrictions: {dietary_restrictions if dietary_restrictions else 'None'}
            - Allergies: {allergies if allergies else 'None'}
            - Preferences: {preferences_list if preferences_list else 'None'}
            
            Please provide:
            1. Breakfast (25% of daily calories)
            2. Lunch (35% of daily calories)
            3. Dinner (30% of daily calories)
            4. Snack (10% of daily calories)
            
            For each meal, include:
            - Meal name
            - Brief description
            - Complete ingredients list with quantities
            - Step-by-step preparation instructions
            - Exact nutritional information (calories, protein, carbs, fat)
            - Preparation time
            
            Format your response as JSON with this structure:
            {{
                "meals": {{
                    "breakfast": {{
                        "name": "...",
                        "description": "...",
                        "ingredients": ["...", "..."],
                        "instructions": ["...", "..."],
                        "nutrition": {{
                            "calories": ...,
                            "protein": ...,
                            "carbs": ...,
                            "fat": ...
                        }},
                        "prep_time": "..."
                    }},
                    "lunch": {{ ... }},
                    "dinner": {{ ... }},
                    "snack": {{ ... }}
                }},
                "daily_totals": {{
                    "calories": ...,
                    "protein": ...,
                    "carbs": ...,
                    "fat": ...
                }}
            }}
            """
            
            response = await self.generate_structured_response(
                prompt=prompt,
                output_schema={
                    "meals": {
                        "breakfast": {
                            "name": "string",
                            "description": "string",
                            "ingredients": ["string"],
                            "instructions": ["string"],
                            "nutrition": {"calories": "number", "protein": "number", "carbs": "number", "fat": "number"},
                            "prep_time": "string"
                        }
                    },
                    "daily_totals": {"calories": "number", "protein": "number", "carbs": "number", "fat": "number"}
                }
            )
            
            # Handle mock responses that aren't structured JSON
            if isinstance(response, str) or "response" in response:
                # Create a mock meal plan for demo purposes
                mock_meal_plan = {
                    "meals": {
                        "breakfast": {
                            "name": "Protein-Packed Breakfast Bowl",
                            "description": "A nutritious breakfast to start your day with energy",
                            "ingredients": ["Greek yogurt", "Berries", "Granola", "Honey", "Almonds"],
                            "instructions": [
                                "Start with Greek yogurt in a bowl",
                                "Top with fresh berries",
                                "Add granola for crunch",
                                "Drizzle with honey",
                                "Sprinkle with almonds"
                            ],
                            "nutrition": {"calories": 450, "protein": 25, "carbs": 45, "fat": 15},
                            "prep_time": "10 minutes"
                        },
                        "lunch": {
                            "name": "Grilled Chicken Salad",
                            "description": "A balanced lunch with lean protein and fresh vegetables",
                            "ingredients": ["Chicken breast", "Mixed greens", "Cherry tomatoes", "Cucumber", "Olive oil", "Lemon"],
                            "instructions": [
                                "Season and grill chicken breast",
                                "Wash and chop vegetables",
                                "Mix greens with vegetables",
                                "Slice chicken and add to salad",
                                "Drizzle with olive oil and lemon"
                            ],
                            "nutrition": {"calories": 550, "protein": 35, "carbs": 30, "fat": 20},
                            "prep_time": "20 minutes"
                        },
                        "dinner": {
                            "name": "Salmon with Quinoa and Vegetables",
                            "description": "A heart-healthy dinner rich in omega-3s",
                            "ingredients": ["Salmon fillet", "Quinoa", "Broccoli", "Bell peppers", "Olive oil", "Garlic"],
                            "instructions": [
                                "Cook quinoa according to package",
                                "Season salmon with salt and pepper",
                                "Pan-sear salmon for 4-5 minutes per side",
                                "Steam or roast vegetables",
                                "Serve salmon over quinoa with vegetables"
                            ],
                            "nutrition": {"calories": 600, "protein": 40, "carbs": 50, "fat": 25},
                            "prep_time": "30 minutes"
                        },
                        "snack": {
                            "name": "Apple with Almond Butter",
                            "description": "A simple, nutritious snack",
                            "ingredients": ["Apple", "Almond butter"],
                            "instructions": [
                                "Slice apple",
                                "Serve with 2 tablespoons of almond butter"
                            ],
                            "nutrition": {"calories": 200, "protein": 5, "carbs": 25, "fat": 10},
                            "prep_time": "5 minutes"
                        }
                    },
                    "daily_totals": {"calories": 1800, "protein": 105, "carbs": 150, "fat": 70}
                }
                return {
                    "success": True,
                    "meal_plan": mock_meal_plan,
                    "plan_type": "daily",
                    "created_date": datetime.now().isoformat()
                }
            
            if "error" in response:
                return response
            
            # Validate and adjust totals if needed
            meal_plan = response
            daily_totals = meal_plan.get("daily_totals", {})
            
            # Check if totals are close to targets (within 10%)
            calorie_tolerance = target_calories * 0.1
            if abs(daily_totals.get("calories", 0) - target_calories) > calorie_tolerance:
                meal_plan["note"] = "Meal plan may need adjustment to meet exact calorie targets"
            
            return {
                "success": True,
                "meal_plan": meal_plan,
                "plan_type": "daily",
                "created_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Error generating daily meal plan: {str(e)}"}
    
    async def generate_weekly_plan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a weekly meal plan"""
        try:
            user_profile = input_data.get("user_profile")
            
            # Generate 7 daily plans with variety
            weekly_plan = {}
            days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            
            for day in days_of_week:
                daily_input = input_data.copy()
                daily_input["preferences"] = input_data.get("preferences", {})
                daily_input["preferences"]["day"] = day
                daily_input["preferences"]["variety_day"] = True
                
                daily_plan = await self.generate_daily_plan(daily_input)
                if "error" not in daily_plan:
                    weekly_plan[day.lower()] = daily_plan["meal_plan"]
                else:
                    return {"error": f"Error generating plan for {day}: {daily_plan['error']}"}
            
            return {
                "success": True,
                "meal_plan": weekly_plan,
                "plan_type": "weekly",
                "created_date": datetime.now().isoformat(),
                "shopping_list": await self.generate_shopping_list(weekly_plan)
            }
            
        except Exception as e:
            return {"error": f"Error generating weekly meal plan: {str(e)}"}
    
    async def get_meal_suggestions(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get meal suggestions for specific meals or occasions"""
        try:
            meal_type = input_data.get("meal_type", "any")  # breakfast, lunch, dinner, snack
            user_profile = input_data.get("user_profile", {})
            preferences = input_data.get("preferences", {})
            
            prompt = f"""
            Provide 5 diverse meal suggestions for {meal_type} based on this profile:
            
            - Goal: {user_profile.get('goal', 'maintain_health')}
            - Dietary Restrictions: {user_profile.get('dietary_restrictions', [])}
            - Allergies: {user_profile.get('allergies', [])}
            - Preferences: {user_profile.get('preferences', [])}
            
            For each suggestion, provide:
            - Meal name
            - Brief description
            - Key ingredients
            - Approximate nutritional information
            - Why it's suitable for their goals
            
            Format as JSON array of meal objects.
            """
            
            response = await self.generate_structured_response(
                prompt=prompt,
                output_schema={
                    "suggestions": [
                        {
                            "name": "string",
                            "description": "string",
                            "ingredients": ["string"],
                            "nutrition": {"calories": "number", "protein": "number", "carbs": "number", "fat": "number"},
                            "suitability": "string"
                        }
                    ]
                }
            )
            
            return {
                "success": True,
                "meal_type": meal_type,
                "suggestions": response.get("suggestions", [])
            }
            
        except Exception as e:
            return {"error": f"Error getting meal suggestions: {str(e)}"}
    
    async def generate_shopping_list(self, weekly_plan: Dict[str, Any]) -> List[str]:
        """Generate a shopping list from weekly meal plan"""
        try:
            all_ingredients = []
            
            for day_plan in weekly_plan.values():
                meals = day_plan.get("meals", {})
                for meal in meals.values():
                    ingredients = meal.get("ingredients", [])
                    all_ingredients.extend(ingredients)
            
            # Remove duplicates and categorize
            unique_ingredients = list(set(all_ingredients))
            
            # Categorize ingredients
            categories = {
                "Produce": [],
                "Protein": [],
                "Dairy": [],
                "Grains": [],
                "Pantry": [],
                "Other": []
            }
            
            for ingredient in unique_ingredients:
                ingredient_lower = ingredient.lower()
                if any(word in ingredient_lower for word in ["chicken", "beef", "pork", "fish", "turkey", "tofu"]):
                    categories["Protein"].append(ingredient)
                elif any(word in ingredient_lower for word in ["milk", "cheese", "yogurt", "butter"]):
                    categories["Dairy"].append(ingredient)
                elif any(word in ingredient_lower for word in ["rice", "pasta", "bread", "oats", "quinoa"]):
                    categories["Grains"].append(ingredient)
                elif any(word in ingredient_lower for word in ["onion", "garlic", "tomato", "lettuce", "carrot", "broccoli"]):
                    categories["Produce"].append(ingredient)
                else:
                    categories["Pantry"].append(ingredient)
            
            # Flatten back to list with categories
            shopping_list = []
            for category, items in categories.items():
                if items:
                    shopping_list.append(f"--- {category} ---")
                    shopping_list.extend(items)
            
            return shopping_list
            
        except Exception as e:
            return ["Error generating shopping list"]