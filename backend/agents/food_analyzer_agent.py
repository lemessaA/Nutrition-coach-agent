from typing import Dict, Any, List
from agents.base import BaseAgent
from tools.food_database import food_database
import re


class FoodAnalyzerAgent(BaseAgent):
    """Agent for analyzing food and calculating nutritional information"""
    
    def __init__(self):
        super().__init__("Food Analyzer Agent")
    
    def get_system_prompt(self) -> str:
        return """You are a nutrition expert specializing in food analysis and nutritional calculations.
        Your role is to:
        1. Analyze food inputs and accurately calculate calories and macronutrients
        2. Provide detailed nutritional breakdowns
        3. Offer insights about the nutritional quality of foods
        4. Suggest healthier alternatives when appropriate
        5. Explain nutritional concepts in simple terms
        
        Always be precise with calculations and provide context for the nutritional information.
        When data is not available, clearly state the limitations and suggest alternatives."""
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process food analysis requests"""
        action = input_data.get("action", "analyze")
        
        if action == "analyze":
            return await self.analyze_food(input_data)
        elif action == "compare":
            return await self.compare_foods(input_data)
        elif action == "meal_analysis":
            return await self.analyze_meal(input_data)
        elif action == "nutrition_insights":
            return await self.get_nutrition_insights(input_data)
        else:
            return {"error": f"Unknown action: {action}"}
    
    async def analyze_food(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single food item"""
        try:
            food_input = input_data.get("food_input", "")
            serving_size = input_data.get("serving_size", "")
            
            if not food_input:
                return {"error": "Food input is required"}
            
            # Parse the food input
            foods = food_database.analyze_meal_string(food_input)
            
            if not foods:
                return {"error": "Could not identify any foods in the input"}
            
            # Calculate totals
            totals = food_database.calculate_totals(foods)
            
            # Get nutritional insights
            insights = await self._generate_nutrition_insights(foods, totals)
            
            # Format response
            analysis = {
                "food_input": food_input,
                "serving_size": serving_size,
                "foods_analyzed": foods,
                "total_nutrition": totals,
                "insights": insights,
                "analysis_timestamp": self._get_timestamp()
            }
            
            return {
                "success": True,
                "analysis": analysis
            }
            
        except Exception as e:
            return {"error": f"Error analyzing food: {str(e)}"}
    
    async def analyze_meal(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a complete meal"""
        try:
            meal_description = input_data.get("meal_description", "")
            meal_type = input_data.get("meal_type", "general")  # breakfast, lunch, dinner, snack
            
            if not meal_description:
                return {"error": "Meal description is required"}
            
            # Parse the meal
            foods = food_database.analyze_meal_string(meal_description)
            
            if not foods:
                return {"error": "Could not identify any foods in the meal"}
            
            # Calculate totals
            totals = food_database.calculate_totals(foods)
            
            # Get meal-specific insights
            meal_insights = await self._generate_meal_insights(foods, totals, meal_type)
            
            # Calculate macro percentages
            macro_percentages = self._calculate_macro_percentages(totals)
            
            # Rate the meal
            meal_rating = self._rate_meal(totals, meal_type)
            
            analysis = {
                "meal_description": meal_description,
                "meal_type": meal_type,
                "foods_analyzed": foods,
                "total_nutrition": totals,
                "macro_percentages": macro_percentages,
                "meal_rating": meal_rating,
                "insights": meal_insights,
                "suggestions": await self._get_meal_suggestions(totals, meal_type),
                "analysis_timestamp": self._get_timestamp()
            }
            
            return {
                "success": True,
                "analysis": analysis
            }
            
        except Exception as e:
            return {"error": f"Error analyzing meal: {str(e)}"}
    
    async def compare_foods(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare multiple foods"""
        try:
            foods_to_compare = input_data.get("foods", [])
            
            if len(foods_to_compare) < 2:
                return {"error": "At least 2 foods are required for comparison"}
            
            comparison_results = []
            
            for food_input in foods_to_compare:
                foods = food_database.analyze_meal_string(food_input)
                if foods:
                    totals = food_database.calculate_totals(foods)
                    comparison_results.append({
                        "food_input": food_input,
                        "nutrition": totals,
                        "foods_analyzed": foods
                    })
            
            # Generate comparison insights
            comparison_insights = await self._generate_comparison_insights(comparison_results)
            
            return {
                "success": True,
                "comparison": {
                    "foods": comparison_results,
                    "insights": comparison_insights,
                    "comparison_timestamp": self._get_timestamp()
                }
            }
            
        except Exception as e:
            return {"error": f"Error comparing foods: {str(e)}"}
    
    async def get_nutrition_insights(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get insights about nutritional data"""
        try:
            nutrition_data = input_data.get("nutrition_data", {})
            context = input_data.get("context", "")
            
            if not nutrition_data:
                return {"error": "Nutrition data is required"}
            
            insights = await self._generate_nutrition_insights([], nutrition_data)
            
            return {
                "success": True,
                "insights": insights,
                "context": context
            }
            
        except Exception as e:
            return {"error": f"Error generating nutrition insights: {str(e)}"}
    
    def _calculate_macro_percentages(self, totals: Dict[str, float]) -> Dict[str, float]:
        """Calculate macronutrient percentages"""
        calories = totals.get("calories", 0)
        if calories == 0:
            return {"protein": 0, "carbs": 0, "fat": 0}
        
        protein_calories = totals.get("protein", 0) * 4
        carbs_calories = totals.get("carbs", 0) * 4
        fat_calories = totals.get("fat", 0) * 9
        
        return {
            "protein": round((protein_calories / calories) * 100, 1),
            "carbs": round((carbs_calories / calories) * 100, 1),
            "fat": round((fat_calories / calories) * 100, 1)
        }
    
    def _rate_meal(self, totals: Dict[str, float], meal_type: str) -> Dict[str, Any]:
        """Rate a meal based on nutritional quality"""
        calories = totals.get("calories", 0)
        protein = totals.get("protein", 0)
        fiber = totals.get("fiber", 0)
        sodium = totals.get("sodium", 0)
        
        # Rating criteria
        score = 0
        feedback = []
        
        # Protein rating
        if meal_type in ["breakfast", "lunch", "dinner"]:
            if protein >= 20:
                score += 2
                feedback.append("Good protein content")
            elif protein >= 10:
                score += 1
                feedback.append("Moderate protein content")
            else:
                feedback.append("Low protein content")
        
        # Fiber rating
        if fiber >= 5:
            score += 2
            feedback.append("High fiber content")
        elif fiber >= 3:
            score += 1
            feedback.append("Moderate fiber content")
        else:
            feedback.append("Low fiber content")
        
        # Sodium rating
        if sodium <= 600:
            score += 1
            feedback.append("Appropriate sodium levels")
        else:
            feedback.append("High sodium content")
        
        # Calorie rating (based on meal type)
        calorie_ranges = {
            "breakfast": (300, 500),
            "lunch": (400, 700),
            "dinner": (400, 700),
            "snack": (100, 300)
        }
        
        if meal_type in calorie_ranges:
            min_cal, max_cal = calorie_ranges[meal_type]
            if min_cal <= calories <= max_cal:
                score += 1
                feedback.append("Appropriate calorie range")
            else:
                feedback.append(f"Calorie count {'high' if calories > max_cal else 'low'} for {meal_type}")
        
        # Overall rating
        if score >= 5:
            rating = "Excellent"
        elif score >= 4:
            rating = "Good"
        elif score >= 3:
            rating = "Fair"
        else:
            rating = "Needs Improvement"
        
        return {
            "score": score,
            "max_score": 6,
            "rating": rating,
            "feedback": feedback
        }
    
    async def _generate_nutrition_insights(self, foods: List[Dict], totals: Dict[str, float]) -> List[str]:
        """Generate insights about the nutritional content"""
        insights = []
        
        calories = totals.get("calories", 0)
        protein = totals.get("protein", 0)
        carbs = totals.get("carbs", 0)
        fat = totals.get("fat", 0)
        fiber = totals.get("fiber", 0)
        
        # Calorie insights
        if calories > 500:
            insights.append("This is a calorie-dense meal, suitable as a main meal")
        elif calories < 200:
            insights.append("This is a light meal, suitable as a snack")
        else:
            insights.append("This has moderate calories, suitable for a balanced meal")
        
        # Protein insights
        if protein >= 25:
            insights.append("High in protein - excellent for muscle maintenance and satiety")
        elif protein >= 15:
            insights.append("Good protein content - supports muscle health")
        else:
            insights.append("Consider adding more protein for better satiety")
        
        # Fiber insights
        if fiber >= 5:
            insights.append("High in fiber - great for digestive health")
        elif fiber >= 3:
            insights.append("Moderate fiber content")
        else:
            insights.append("Low in fiber - consider adding vegetables or whole grains")
        
        # Fat insights
        fat_percentage = (fat * 9 / calories * 100) if calories > 0 else 0
        if fat_percentage > 40:
            insights.append("High in fat - ensure healthy fat sources")
        elif fat_percentage < 20:
            insights.append("Low in fat - consider adding healthy fats")
        
        return insights
    
    async def _generate_meal_insights(self, foods: List[Dict], totals: Dict[str, float], meal_type: str) -> List[str]:
        """Generate meal-specific insights"""
        insights = await self._generate_nutrition_insights(foods, totals)
        
        # Meal-type specific insights
        if meal_type == "breakfast":
            if totals.get("protein", 0) >= 15:
                insights.append("Good protein content for sustained morning energy")
            if totals.get("carbs", 0) >= 30:
                insights.append("Adequate carbohydrates for morning fuel")
        
        elif meal_type == "post_workout":
            if totals.get("protein", 0) >= 20:
                insights.append("Excellent protein content for muscle recovery")
            if totals.get("carbs", 0) >= 30:
                insights.append("Good carbohydrate content for glycogen replenishment")
        
        return insights
    
    async def _generate_comparison_insights(self, comparison_results: List[Dict]) -> List[str]:
        """Generate insights from food comparison"""
        insights = []
        
        if len(comparison_results) >= 2:
            # Compare calories
            calories = [item["nutrition"].get("calories", 0) for item in comparison_results]
            max_cal_idx = calories.index(max(calories))
            min_cal_idx = calories.index(min(calories))
            
            insights.append(f"{comparison_results[max_cal_idx]['food_input']} has the most calories ({max(calories)} kcal)")
            insights.append(f"{comparison_results[min_cal_idx]['food_input']} has the fewest calories ({min(calories)} kcal)")
            
            # Compare protein
            proteins = [item["nutrition"].get("protein", 0) for item in comparison_results]
            max_prot_idx = proteins.index(max(proteins))
            
            insights.append(f"{comparison_results[max_prot_idx]['food_input']} is highest in protein ({max(proteins)}g)")
        
        return insights
    
    async def _get_meal_suggestions(self, totals: Dict[str, float], meal_type: str) -> List[str]:
        """Get suggestions for improving the meal"""
        suggestions = []
        
        if totals.get("protein", 0) < 15:
            suggestions.append("Add lean protein like chicken, fish, or legumes")
        
        if totals.get("fiber", 0) < 3:
            suggestions.append("Include more vegetables or whole grains for fiber")
        
        if totals.get("sodium", 0) > 600:
            suggestions.append("Reduce sodium by using herbs and spices instead of salt")
        
        return suggestions
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()