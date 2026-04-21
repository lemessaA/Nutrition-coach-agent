from typing import Dict, List, Any, Optional
import json
import re


# Approximate weight (grams) of one typical piece of common foods.
# Used when an input like "1 medium apple" or "2 eggs" has no explicit
# weight unit, so that the count is converted to grams instead of being
# treated literally as "1 gram".
ITEM_WEIGHTS_G: Dict[str, float] = {
    "apple": 182,
    "banana": 118,
    "orange": 131,
    "strawberry": 12,
    "blueberry": 1,
    "grape": 5,
    "egg": 50,
    "eggs": 50,
    "potato": 213,
    "sweet potato": 200,
    "tomato": 123,
    "carrot": 61,
    "onion": 110,
    "bell pepper": 119,
    "cucumber": 301,
    "avocado": 150,
    "bread white": 28,
    "bread whole wheat": 28,
}

# Size qualifiers that should be stripped from the food name and
# optionally scale the item weight.
SIZE_MULTIPLIERS: Dict[str, float] = {
    "small": 0.75,
    "medium": 1.0,
    "large": 1.3,
    "extra": 1.5,
    "jumbo": 1.6,
}


class FoodDatabase:
    """Simple food nutrition database for calorie and macro estimation"""
    
    def __init__(self):
        self.food_data = self._load_food_database()
    
    def _load_food_database(self) -> Dict[str, Dict[str, float]]:
        """Load a comprehensive food database with nutritional information"""
        return {
            # Proteins (per 100g)
            "chicken breast": {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6, "fiber": 0, "sugar": 0, "sodium": 74},
            "chicken thigh": {"calories": 209, "protein": 26, "carbs": 0, "fat": 10.9, "fiber": 0, "sugar": 0, "sodium": 77},
            "beef lean": {"calories": 250, "protein": 26, "carbs": 0, "fat": 15, "fiber": 0, "sugar": 0, "sodium": 60},
            "salmon": {"calories": 208, "protein": 20, "carbs": 0, "fat": 13, "fiber": 0, "sugar": 0, "sodium": 59},
            "tuna": {"calories": 144, "protein": 30, "carbs": 0, "fat": 1, "fiber": 0, "sugar": 0, "sodium": 37},
            "eggs": {"calories": 155, "protein": 13, "carbs": 1.1, "fat": 11, "fiber": 0, "sugar": 1.1, "sodium": 124},
            "greek yogurt": {"calories": 59, "protein": 10, "carbs": 3.6, "fat": 0.4, "fiber": 0, "sugar": 3.6, "sodium": 36},
            "cottage cheese": {"calories": 98, "protein": 11, "carbs": 3.4, "fat": 4.3, "fiber": 0, "sugar": 2.7, "sodium": 364},
            "tofu": {"calories": 76, "protein": 8, "carbs": 1.9, "fat": 4.8, "fiber": 0.3, "sugar": 0.7, "sodium": 7},
            "lentils": {"calories": 116, "protein": 9, "carbs": 20, "fat": 0.4, "fiber": 7.9, "sugar": 1.8, "sodium": 2},
            "black beans": {"calories": 132, "protein": 8.9, "carbs": 24, "fat": 0.5, "fiber": 8.7, "sugar": 0.6, "sodium": 1},
            "chickpeas": {"calories": 164, "protein": 8.9, "carbs": 27, "fat": 2.6, "fiber": 7.6, "sugar": 4.8, "sodium": 7},
            
            # Grains and Starches (per 100g cooked)
            "rice white": {"calories": 130, "protein": 2.7, "carbs": 28, "fat": 0.3, "fiber": 0.4, "sugar": 0.1, "sodium": 1},
            "rice brown": {"calories": 111, "protein": 2.6, "carbs": 23, "fat": 0.9, "fiber": 1.8, "sugar": 0.4, "sodium": 5},
            "pasta": {"calories": 131, "protein": 5, "carbs": 25, "fat": 1.1, "fiber": 1.8, "sugar": 0.6, "sodium": 6},
            "bread whole wheat": {"calories": 247, "protein": 13, "carbs": 41, "fat": 3.4, "fiber": 6, "sugar": 5, "sodium": 491},
            "bread white": {"calories": 265, "protein": 9, "carbs": 49, "fat": 3.2, "fiber": 2.7, "sugar": 5, "sodium": 491},
            "oats": {"calories": 68, "protein": 2.4, "carbs": 12, "fat": 1.4, "fiber": 1.7, "sugar": 0.6, "sodium": 49},
            "quinoa": {"calories": 120, "protein": 4.4, "carbs": 21, "fat": 1.9, "fiber": 2.8, "sugar": 0.9, "sodium": 7},
            "potato": {"calories": 77, "protein": 2, "carbs": 17, "fat": 0.1, "fiber": 2.2, "sugar": 0.8, "sodium": 6},
            "sweet potato": {"calories": 86, "protein": 1.6, "carbs": 20, "fat": 0.1, "fiber": 3, "sugar": 4.2, "sodium": 4},
            
            # Vegetables (per 100g)
            "broccoli": {"calories": 34, "protein": 2.8, "carbs": 7, "fat": 0.4, "fiber": 2.6, "sugar": 1.5, "sodium": 33},
            "spinach": {"calories": 23, "protein": 2.9, "carbs": 3.6, "fat": 0.4, "fiber": 2.2, "sugar": 0.4, "sodium": 79},
            "lettuce": {"calories": 15, "protein": 1.4, "carbs": 2.9, "fat": 0.2, "fiber": 1.3, "sugar": 0.8, "sodium": 28},
            "tomato": {"calories": 18, "protein": 0.9, "carbs": 3.9, "fat": 0.2, "fiber": 1.2, "sugar": 2.6, "sodium": 5},
            "carrot": {"calories": 41, "protein": 0.9, "carbs": 10, "fat": 0.2, "fiber": 2.8, "sugar": 4.7, "sodium": 69},
            "onion": {"calories": 40, "protein": 1.1, "carbs": 9.3, "fat": 0.1, "fiber": 1.7, "sugar": 4.2, "sodium": 4},
            "garlic": {"calories": 149, "protein": 6.4, "carbs": 33, "fat": 0.5, "fiber": 2.1, "sugar": 1, "sodium": 17},
            "bell pepper": {"calories": 31, "protein": 1, "carbs": 7.4, "fat": 0.3, "fiber": 2.5, "sugar": 4.2, "sodium": 4},
            "cucumber": {"calories": 16, "protein": 0.7, "carbs": 3.6, "fat": 0.1, "fiber": 0.5, "sugar": 1.7, "sodium": 2},
            "avocado": {"calories": 160, "protein": 2, "carbs": 9, "fat": 15, "fiber": 6.7, "sugar": 0.7, "sodium": 7},
            
            # Fruits (per 100g)
            "apple": {"calories": 52, "protein": 0.3, "carbs": 14, "fat": 0.2, "fiber": 2.4, "sugar": 10, "sodium": 1},
            "banana": {"calories": 89, "protein": 1.1, "carbs": 23, "fat": 0.3, "fiber": 2.6, "sugar": 12, "sodium": 1},
            "orange": {"calories": 47, "protein": 0.9, "carbs": 12, "fat": 0.1, "fiber": 2.4, "sugar": 9.4, "sodium": 0},
            "strawberry": {"calories": 32, "protein": 0.7, "carbs": 8, "fat": 0.3, "fiber": 2, "sugar": 4.9, "sodium": 1},
            "blueberry": {"calories": 57, "protein": 0.7, "carbs": 14, "fat": 0.3, "fiber": 2.4, "sugar": 10, "sodium": 1},
            "grape": {"calories": 69, "protein": 0.7, "carbs": 18, "fat": 0.2, "fiber": 0.9, "sugar": 16, "sodium": 1},
            
            # Dairy and Alternatives
            "milk": {"calories": 42, "protein": 3.4, "carbs": 5, "fat": 1, "fiber": 0, "sugar": 5, "sodium": 44},
            "cheese cheddar": {"calories": 402, "protein": 25, "carbs": 1.3, "fat": 33, "fiber": 0, "sugar": 0.6, "sodium": 621},
            "cheese mozzarella": {"calories": 280, "protein": 22, "carbs": 2.2, "fat": 22, "fiber": 0, "sugar": 1, "sodium": 627},
            "yogurt plain": {"calories": 59, "protein": 10, "carbs": 3.6, "fat": 0.4, "fiber": 0, "sugar": 3.6, "sodium": 36},
            
            # Nuts and Seeds (per 100g)
            "almonds": {"calories": 579, "protein": 21, "carbs": 22, "fat": 50, "fiber": 12, "sugar": 4, "sodium": 1},
            "walnuts": {"calories": 654, "protein": 15, "carbs": 14, "fat": 65, "fiber": 6.7, "sugar": 2.6, "sodium": 2},
            "peanut butter": {"calories": 588, "protein": 25, "carbs": 20, "fat": 50, "fiber": 6, "sugar": 9, "sodium": 459},
            "chia seeds": {"calories": 486, "protein": 17, "carbs": 42, "fat": 31, "fiber": 34, "sugar": 0, "sodium": 16},
            "flax seeds": {"calories": 534, "protein": 18, "carbs": 29, "fat": 42, "fiber": 27, "sugar": 1.6, "sodium": 30},
            
            # Oils and Fats (per 100g)
            "olive oil": {"calories": 884, "protein": 0, "carbs": 0, "fat": 100, "fiber": 0, "sugar": 0, "sodium": 2},
            "coconut oil": {"calories": 862, "protein": 0, "carbs": 0, "fat": 100, "fiber": 0, "sugar": 0, "sodium": 0},
            "butter": {"calories": 717, "protein": 0.9, "carbs": 0.1, "fat": 81, "fiber": 0, "sugar": 0.1, "sodium": 643},
            
            # Common Meals/Combos
            "rice and beans": {"calories": 214, "protein": 8, "carbs": 45, "fat": 1.4, "fiber": 5.3, "sugar": 1.5, "sodium": 3},
            "chicken stir fry": {"calories": 185, "protein": 25, "carbs": 8, "fat": 6, "fiber": 2, "sugar": 3, "sodium": 400},
            "salad with chicken": {"calories": 220, "protein": 30, "carbs": 5, "fat": 8, "fiber": 4, "sugar": 3, "sodium": 300},
            "oatmeal with berries": {"calories": 150, "protein": 5, "carbs": 28, "fat": 3, "fiber": 5, "sugar": 8, "sodium": 50},
        }
    
    def find_food(self, food_name: str) -> Optional[Dict[str, float]]:
        """Find food in database with fuzzy matching"""
        food_name = food_name.lower().strip()
        
        # Direct match
        if food_name in self.food_data:
            return self.food_data[food_name]
        
        # Partial match
        for key in self.food_data:
            if food_name in key or key in food_name:
                return self.food_data[key]
        
        # Word matching
        food_words = food_name.split()
        for key in self.food_data:
            key_words = key.split()
            if any(word in key for word in food_words) or any(word in food_name for word in key_words):
                return self.food_data[key]
        
        return None
    
    def get_food_info(self, food_name: str, quantity: float = 100, unit: str = "g", size: Optional[str] = None) -> Dict[str, Any]:
        """Get nutritional information for a food with quantity.

        Strategy:
          1. Try the local in-memory dataset (zero latency, zero cost).
          2. If not found, query the external `FoodProviderRegistry`
             (USDA → Nutritionix → Open Food Facts) with caching.
          3. If still nothing, return a clear miss payload.
        """
        food_data = self.find_food(food_name)
        source = "local"

        if not food_data:
            external = _lookup_external_sync(food_name)
            if external is not None:
                food_data = external["nutrition"]
                source = external["source"]

        if not food_data:
            return {"found": False, "message": f"Food '{food_name}' not found in database"}
        
        unit_l = (unit or "g").lower()
        
        # Convert quantity to grams if needed
        if unit_l in ["oz", "ounce"]:
            quantity_g = quantity * 28.35
        elif unit_l in ["lb", "pound"]:
            quantity_g = quantity * 453.59
        elif unit_l in ["cup", "cups"]:
            # Approximate conversion for common ingredients
            if "rice" in food_name:
                quantity_g = quantity * 185
            elif "flour" in food_name:
                quantity_g = quantity * 120
            else:
                quantity_g = quantity * 240  # General approximation
        elif unit_l in ["item", "items", "piece", "pieces", "whole", "ct", "count"]:
            per_item = self._per_item_weight(food_name)
            mult = SIZE_MULTIPLIERS.get((size or "").lower(), 1.0)
            quantity_g = quantity * per_item * mult
        else:
            quantity_g = quantity
        
        # Calculate nutrition based on quantity
        multiplier = quantity_g / 100
        nutrition = {}
        for key, value in food_data.items():
            nutrition[key] = round(value * multiplier, 1)
        
        return {
            "found": True,
            "food_name": food_name,
            "quantity": quantity,
            "unit": unit,
            "quantity_grams": quantity_g,
            "nutrition": nutrition,
            "source": source,
        }
    
    def _per_item_weight(self, food_name: str) -> float:
        """Approximate weight (grams) of a single item of the given food."""
        name = (food_name or "").lower().strip()
        if name in ITEM_WEIGHTS_G:
            return ITEM_WEIGHTS_G[name]
        for key, grams in ITEM_WEIGHTS_G.items():
            if key in name or name in key:
                return grams
        # Reasonable fallback: assume a typical serving of ~100g
        return 100.0
    
    def analyze_meal_string(self, meal_string: str) -> List[Dict[str, Any]]:
        """Parse a meal string and extract food items with quantities"""
        foods = []
        
        # Common patterns for food quantities
        patterns = [
            r'(\d+\.?\d*)\s*(g|kg|oz|lb|cup|cups|tbsp|tsp|tablespoon|teaspoon)s?\s*(.+?)(?:,|$|\n)',
            r'(.+?)\s+(\d+\.?\d*)\s*(g|kg|oz|lb|cup|cups|tbsp|tsp|tablespoon|teaspoon)s?\s*(?:,|$|\n)',
            r'(\d+)\s*(.+?)(?:,|$|\n)',  # Just number + food name
        ]
        
        # Split by common separators
        items = re.split(r'[,;\n]|and ', meal_string)
        
        for item in items:
            item = item.strip()
            if not item:
                continue
            
            matched = False
            
            for pattern in patterns:
                match = re.search(pattern, item, re.IGNORECASE)
                if match:
                    size = None
                    if pattern == patterns[2]:  # Just number + food (no weight unit)
                        quantity = float(match.group(1))
                        raw_name = match.group(2).strip()
                        # Detect size qualifiers like "medium", "large", ...
                        tokens = raw_name.split()
                        if tokens and tokens[0].lower() in SIZE_MULTIPLIERS:
                            size = tokens[0].lower()
                            raw_name = " ".join(tokens[1:]).strip() or raw_name
                        food_name = raw_name
                        # Treat the count as "items" rather than grams so that
                        # "1 medium apple" becomes ~1 item, not 1 gram.
                        unit = "item"
                    else:
                        groups = match.groups()
                        if len(groups) == 3:
                            if groups[0].replace('.', '').isdigit():
                                quantity = float(groups[0])
                                unit = groups[1]
                                food_name = groups[2].strip()
                            else:
                                food_name = groups[0].strip()
                                quantity = float(groups[1])
                                unit = groups[2]
                        else:
                            continue
                    
                    food_info = self.get_food_info(food_name, quantity, unit, size=size)
                    foods.append(food_info)
                    matched = True
                    break
            
            # If no pattern matched, try to find the food without quantity
            if not matched:
                food_info = self.get_food_info(item, 100, "g")  # Default 100g
                foods.append(food_info)
        
        return foods
    
    def calculate_totals(self, foods: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate total nutrition from a list of foods"""
        totals = {
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0,
            "fiber": 0,
            "sugar": 0,
            "sodium": 0
        }
        
        for food in foods:
            if food.get("found") and "nutrition" in food:
                nutrition = food["nutrition"]
                for key in totals:
                    if key in nutrition:
                        totals[key] += nutrition[key]
        
        # Round totals
        for key in totals:
            totals[key] = round(totals[key], 1)
        
        return totals


# Global food database instance
food_database = FoodDatabase()
