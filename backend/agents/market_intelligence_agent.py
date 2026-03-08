from typing import Dict, Any, List
import requests
import json
from datetime import datetime, timedelta
from agents.base import BaseAgent


class MarketIntelligenceAgent(BaseAgent):
    """Agent for gathering market data on food prices, availability, and trends"""
    
    def __init__(self):
        super().__init__("Market Intelligence Agent")
        self.data_sources = self._initialize_data_sources()
    
    def get_system_prompt(self) -> str:
        return """You are a market intelligence specialist focusing on food pricing and availability.
        Your role is to:
        1. Analyze food price trends and availability
        2. Provide cost-effective nutrition recommendations
        3. Suggest seasonal and locally available alternatives
        4. Help users make budget-conscious healthy choices
        5. Identify market trends affecting nutrition planning
        
        Always provide practical, actionable advice that considers both nutrition and budget.
        Be transparent about data limitations and regional variations."""
    
    def _initialize_data_sources(self) -> Dict[str, Any]:
        """Initialize available data sources and APIs"""
        return {
            "usda_fdc": {
                "url": "https://api.nal.usda.gov/fdc/v1/",
                "api_key": None,  # Will be set from config
                "description": "USDA Food Data Central"
            },
            "open_food_facts": {
                "url": "https://world.openfoodfacts.org/api/v2/",
                "description": "Open Food Facts database"
            },
            "local_markets": {
                "data": {},  # Will be populated with local market data
                "description": "Local market price data"
            }
        }
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process market intelligence requests"""
        action = input_data.get("action", "search")
        
        if action == "search_prices":
            return await self.search_food_prices(input_data)
        elif action == "availability_check":
            return await self.check_availability(input_data)
        elif action == "seasonal_recommendations":
            return await self.get_seasonal_recommendations(input_data)
        elif action == "budget_analysis":
            return await self.analyze_budget_options(input_data)
        elif action == "market_trends":
            return await self.get_market_trends(input_data)
        elif action == "ingest_data":
            return await self.ingest_market_data(input_data)
        else:
            return {"error": f"Unknown action: {action}"}
    
    async def search_food_prices(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Search for current food prices"""
        try:
            food_items = input_data.get("food_items", [])
            location = input_data.get("location", "general")
            price_range = input_data.get("price_range", "all")
            
            if not food_items:
                return {"error": "Food items are required for price search"}
            
            price_results = []
            
            for item in food_items:
                # Search in local database first
                local_price = await self._search_local_prices(item, location)
                
                # If not found locally, search external APIs
                if not local_price:
                    external_price = await self._search_external_prices(item)
                    price_results.append(external_price)
                else:
                    price_results.append(local_price)
            
            # Analyze price trends
            price_analysis = await self._analyze_price_trends(price_results)
            
            # Suggest alternatives if needed
            alternatives = await self._suggest_alternatives(food_items, price_results, price_range)
            
            return {
                "success": True,
                "food_items": food_items,
                "location": location,
                "price_results": price_results,
                "price_analysis": price_analysis,
                "alternatives": alternatives,
                "search_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Error searching food prices: {str(e)}"}
    
    async def check_availability(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check food availability in markets"""
        try:
            food_items = input_data.get("food_items", [])
            location = input_data.get("location", "general")
            season = input_data.get("season", "current")
            
            availability_results = []
            
            for item in food_items:
                availability = await self._check_item_availability(item, location, season)
                availability_results.append(availability)
            
            # Generate availability insights
            insights = await self._generate_availability_insights(availability_results)
            
            return {
                "success": True,
                "food_items": food_items,
                "location": location,
                "season": season,
                "availability_results": availability_results,
                "insights": insights,
                "check_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Error checking availability: {str(e)}"}
    
    async def get_seasonal_recommendations(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get seasonal food recommendations"""
        try:
            season = input_data.get("season", "current")
            location = input_data.get("location", "general")
            user_preferences = input_data.get("user_preferences", {})
            
            # Get seasonal produce
            seasonal_produce = await self._get_seasonal_produce(season, location)
            
            # Filter by preferences
            filtered_produce = await self._filter_by_preferences(seasonal_produce, user_preferences)
            
            # Generate nutritional insights
            nutritional_benefits = await self._analyze_nutritional_benefits(filtered_produce)
            
            # Suggest recipes
            recipe_suggestions = await self._suggest_seasonal_recipes(filtered_produce, season)
            
            return {
                "success": True,
                "season": season,
                "location": location,
                "seasonal_produce": filtered_produce,
                "nutritional_benefits": nutritional_benefits,
                "recipe_suggestions": recipe_suggestions,
                "recommendation_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Error getting seasonal recommendations: {str(e)}"}
    
    async def analyze_budget_options(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze budget-friendly nutrition options"""
        try:
            budget = input_data.get("budget", 0)
            dietary_requirements = input_data.get("dietary_requirements", {})
            family_size = input_data.get("family_size", 1)
            time_period = input_data.get("time_period", "week")
            
            # Get budget-friendly options
            budget_options = await self._get_budget_options(budget, dietary_requirements, family_size)
            
            # Calculate cost per meal
            cost_analysis = await self._calculate_cost_per_meal(budget_options, family_size, time_period)
            
            # Generate meal plan suggestions
            meal_suggestions = await self._generate_budget_meal_plan(budget_options, dietary_requirements)
            
            # Provide shopping tips
            shopping_tips = await self._generate_budget_shopping_tips(budget_options)
            
            return {
                "success": True,
                "budget": budget,
                "family_size": family_size,
                "time_period": time_period,
                "budget_options": budget_options,
                "cost_analysis": cost_analysis,
                "meal_suggestions": meal_suggestions,
                "shopping_tips": shopping_tips,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Error analyzing budget options: {str(e)}"}
    
    async def get_market_trends(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get current market trends in nutrition"""
        try:
            trend_category = input_data.get("category", "general")
            time_frame = input_data.get("time_frame", "month")
            
            # Analyze market trends
            trends = await self._analyze_market_trends(trend_category, time_frame)
            
            # Generate insights
            insights = await self._generate_trend_insights(trends)
            
            # Predict future trends
            predictions = await self._predict_future_trends(trends)
            
            return {
                "success": True,
                "category": trend_category,
                "time_frame": time_frame,
                "trends": trends,
                "insights": insights,
                "predictions": predictions,
                "trend_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Error getting market trends: {str(e)}"}
    
    async def ingest_market_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest new market data from various sources"""
        try:
            data_source = input_data.get("data_source", "manual")
            data_format = input_data.get("data_format", "json")
            market_data = input_data.get("market_data", {})
            
            # Validate and clean data
            cleaned_data = await self._validate_and_clean_data(market_data, data_format)
            
            # Store in database
            storage_result = await self._store_market_data(cleaned_data, data_source)
            
            # Update indexes
            index_update = await self._update_search_indexes(cleaned_data)
            
            return {
                "success": True,
                "data_source": data_source,
                "records_processed": len(cleaned_data) if isinstance(cleaned_data, list) else 1,
                "storage_result": storage_result,
                "index_update": index_update,
                "ingestion_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Error ingesting market data: {str(e)}"}
    
    async def _search_local_prices(self, item: str, location: str) -> Dict[str, Any]:
        """Search local price database"""
        # This would query the local database
        # For now, return mock data
        return {
            "item": item,
            "location": location,
            "price": 2.99,
            "unit": "lb",
            "source": "local_database",
            "last_updated": datetime.now().isoformat(),
            "availability": "in_stock"
        }
    
    async def _search_external_prices(self, item: str) -> Dict[str, Any]:
        """Search external APIs for price data"""
        try:
            # This would make actual API calls
            # For now, return mock data
            return {
                "item": item,
                "location": "national_average",
                "price": 3.49,
                "unit": "lb",
                "source": "external_api",
                "last_updated": datetime.now().isoformat(),
                "availability": "in_stock"
            }
        except Exception as e:
            return {
                "item": item,
                "error": f"Could not fetch price data: {str(e)}"
            }
    
    async def _analyze_price_trends(self, price_results: List[Dict]) -> Dict[str, Any]:
        """Analyze price trends from results"""
        if not price_results:
            return {"trend": "no_data", "analysis": "No price data available"}
        
        # Simple trend analysis
        prices = [r.get("price", 0) for r in price_results if "price" in r]
        if not prices:
            return {"trend": "no_data", "analysis": "No valid price data"}
        
        avg_price = sum(prices) / len(prices)
        
        return {
            "trend": "stable",  # Would be calculated from historical data
            "average_price": round(avg_price, 2),
            "price_range": {"min": min(prices), "max": max(prices)},
            "data_points": len(prices)
        }
    
    async def _suggest_alternatives(self, food_items: List[str], price_results: List[Dict], price_range: str) -> List[Dict[str, Any]]:
        """Suggest budget-friendly alternatives"""
        alternatives = []
        
        # Simple alternative suggestions
        alternatives_map = {
            "salmon": ["canned salmon", "mackerel", "sardines"],
            "beef": ["chicken", "turkey", "pork"],
            "fresh berries": ["frozen berries", "apples", "bananas"]
        }
        
        for item in food_items:
            if item.lower() in alternatives_map:
                for alt in alternatives_map[item.lower()]:
                    alternatives.append({
                        "original_item": item,
                        "alternative": alt,
                        "reason": "More budget-friendly option",
                        "estimated_savings": "20-30%"
                    })
        
        return alternatives
    
    async def _check_item_availability(self, item: str, location: str, season: str) -> Dict[str, Any]:
        """Check availability of a specific item"""
        # Mock availability check
        seasonal_items = {
            "spring": ["asparagus", "strawberries", "spinach"],
            "summer": ["tomatoes", "corn", "watermelon"],
            "fall": ["pumpkin", "apples", "brussels sprouts"],
            "winter": ["squash", "citrus", "kale"]
        }
        
        is_seasonal = any(item.lower() in seasonal_items.get(s, []) for s in seasonal_items)
        
        return {
            "item": item,
            "location": location,
            "season": season,
            "availability": "high" if is_seasonal else "moderate",
            "is_seasonal": is_seasonal,
            "quality": "excellent" if is_seasonal else "good"
        }
    
    async def _get_seasonal_produce(self, season: str, location: str) -> List[Dict[str, Any]]:
        """Get seasonal produce for given season and location"""
        seasonal_data = {
            "spring": [
                {"name": "asparagus", "nutrients": ["folate", "vitamin K"], "price": "moderate"},
                {"name": "strawberries", "nutrients": ["vitamin C", "fiber"], "price": "low"},
                {"name": "spinach", "nutrients": ["iron", "vitamin A"], "price": "low"}
            ],
            "summer": [
                {"name": "tomatoes", "nutrients": ["lycopene", "vitamin C"], "price": "low"},
                {"name": "corn", "nutrients": ["fiber", "B vitamins"], "price": "low"},
                {"name": "watermelon", "nutrients": ["vitamin A", "hydration"], "price": "low"}
            ],
            "fall": [
                {"name": "pumpkin", "nutrients": ["vitamin A", "fiber"], "price": "low"},
                {"name": "apples", "nutrients": ["fiber", "vitamin C"], "price": "low"},
                {"name": "brussels sprouts", "nutrients": ["vitamin K", "vitamin C"], "price": "moderate"}
            ],
            "winter": [
                {"name": "squash", "nutrients": ["vitamin A", "fiber"], "price": "low"},
                {"name": "citrus", "nutrients": ["vitamin C", "folate"], "price": "moderate"},
                {"name": "kale", "nutrients": ["vitamin K", "vitamin A"], "price": "low"}
            ]
        }
        
        return seasonal_data.get(season, seasonal_data["spring"])
    
    async def _filter_by_preferences(self, produce: List[Dict], preferences: Dict) -> List[Dict]:
        """Filter produce by user preferences"""
        if not preferences:
            return produce
        
        filtered = produce.copy()
        
        # Filter by dietary restrictions
        if "organic" in preferences and preferences["organic"]:
            # In real implementation, would filter for organic options
            pass
        
        return filtered
    
    async def _analyze_nutritional_benefits(self, produce: List[Dict]) -> Dict[str, Any]:
        """Analyze nutritional benefits of seasonal produce"""
        all_nutrients = []
        for item in produce:
            all_nutrients.extend(item.get("nutrients", []))
        
        # Count nutrient frequency
        nutrient_count = {}
        for nutrient in all_nutrients:
            nutrient_count[nutrient] = nutrient_count.get(nutrient, 0) + 1
        
        return {
            "top_nutrients": sorted(nutrient_count.items(), key=lambda x: x[1], reverse=True)[:5],
            "total_variety": len(set(all_nutrients)),
            "seasonal_advantage": "Peak nutritional content and flavor"
        }
    
    async def _suggest_seasonal_recipes(self, produce: List[Dict], season: str) -> List[str]:
        """Suggest recipes using seasonal produce"""
        produce_names = [item["name"] for item in produce]
        
        # Simple recipe suggestions based on available produce
        recipes = []
        if "tomatoes" in produce_names and "corn" in produce_names:
            recipes.append("Summer vegetable salad with grilled corn")
        if "pumpkin" in produce_names:
            recipes.append("Roasted pumpkin soup")
        if "apples" in produce_names and "brussels sprouts" in produce_names:
            recipes.append("Apple Brussels sprouts slaw")
        
        return recipes[:3]  # Return top 3 suggestions
    
    async def _get_budget_options(self, budget: float, requirements: Dict, family_size: int) -> List[Dict[str, Any]]:
        """Get budget-friendly food options"""
        # Mock budget options
        return [
            {
                "category": "proteins",
                "options": ["eggs", "beans", "chicken thighs", "canned fish"],
                "weekly_cost": budget * 0.3,
                "servings": family_size * 7
            },
            {
                "category": "vegetables",
                "options": ["frozen vegetables", "seasonal produce", "cabbage", "carrots"],
                "weekly_cost": budget * 0.25,
                "servings": family_size * 7
            },
            {
                "category": "grains",
                "options": ["rice", "oats", "pasta", "potatoes"],
                "weekly_cost": budget * 0.2,
                "servings": family_size * 7
            }
        ]
    
    async def _calculate_cost_per_meal(self, budget_options: List[Dict], family_size: int, time_period: str) -> Dict[str, Any]:
        """Calculate cost per meal"""
        total_weekly_cost = sum(option["weekly_cost"] for option in budget_options)
        meals_per_week = family_size * 21  # 3 meals per day
        
        cost_per_meal = total_weekly_cost / meals_per_week
        
        return {
            "total_weekly_cost": total_weekly_cost,
            "meals_per_week": meals_per_week,
            "cost_per_meal": round(cost_per_meal, 2),
            "cost_per_person_per_day": round(total_weekly_cost / family_size / 7, 2)
        }
    
    async def _generate_budget_meal_plan(self, budget_options: List[Dict], requirements: Dict) -> List[str]:
        """Generate meal plan using budget options"""
        return [
            "Breakfast: Oatmeal with seasonal fruit",
            "Lunch: Bean and vegetable soup",
            "Dinner: Chicken thighs with roasted vegetables",
            "Snacks: Hard-boiled eggs and seasonal fruit"
        ]
    
    async def _generate_budget_shopping_tips(self, budget_options: List[Dict]) -> List[str]:
        """Generate budget shopping tips"""
        return [
            "Buy seasonal produce for best prices and quality",
            "Consider frozen vegetables for convenience and nutrition",
            "Purchase whole grains in bulk for savings",
            "Plan meals around sales and specials",
            "Reduce food waste by using leftovers creatively"
        ]
    
    async def _analyze_market_trends(self, category: str, time_frame: str) -> List[Dict[str, Any]]:
        """Analyze market trends"""
        # Mock trend data
        return [
            {
                "trend": "Plant-based foods",
                "growth": "+25%",
                "description": "Increased demand for plant-based proteins and alternatives"
            },
            {
                "trend": "Local sourcing",
                "growth": "+18%",
                "description": "Growing preference for locally sourced foods"
            },
            {
                "trend": "Sustainable packaging",
                "growth": "+32%",
                "description": "Consumer demand for eco-friendly packaging"
            }
        ]
    
    async def _generate_trend_insights(self, trends: List[Dict]) -> List[str]:
        """Generate insights from market trends"""
        insights = []
        for trend in trends:
            insight = f"{trend['trend']}: {trend['description']} with {trend['growth']} growth"
            insights.append(insight)
        return insights
    
    async def _predict_future_trends(self, trends: List[Dict]) -> List[str]:
        """Predict future market trends"""
        return [
            "Increased focus on functional foods with added health benefits",
            "Growing demand for convenient healthy meal solutions",
            "Expansion of personalized nutrition products"
        ]
    
    async def _validate_and_clean_data(self, data: Dict, format_type: str) -> Dict:
        """Validate and clean incoming market data"""
        # Basic validation
        if format_type == "json":
            if not isinstance(data, dict):
                raise ValueError("Invalid JSON format")
            
            # Ensure required fields
            required_fields = ["food_item", "price", "unit"]
            for field in required_fields:
                if field not in data:
                    data[field] = None
        
        return data
    
    async def _store_market_data(self, data: Dict, source: str) -> Dict[str, Any]:
        """Store market data in database"""
        # This would store in the actual database
        return {
            "status": "stored",
            "records": 1,
            "source": source,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _update_search_indexes(self, data: Dict) -> Dict[str, Any]:
        """Update search indexes for new data"""
        # This would update search indexes
        return {
            "status": "updated",
            "indexes_affected": ["food_items", "prices", "availability"],
            "timestamp": datetime.now().isoformat()
        }
