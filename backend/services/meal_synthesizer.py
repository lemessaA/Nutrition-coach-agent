"""Deterministic, data-driven meal plan synthesizer.

This module is used as a reliable fallback whenever the LLM-generated
structured response is unavailable or malformed. Unlike the previous
hard-coded "mock" plan, every meal here is built from real per-100g
nutrition values in :mod:`tools.food_database` and the portions are
scaled so each meal hits the user's calorie targets while respecting
dietary restrictions and allergies.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from tools.food_database import FoodDatabase


# ---------------------------------------------------------------------------
# Meal templates
# ---------------------------------------------------------------------------
# Each component references a key in ``FoodDatabase.food_data`` so nutrition
# comes straight from the local food catalogue. ``base_g`` is a sensible
# starting portion in grams; the synthesizer scales all components uniformly
# to hit the target calories for the meal slot.

MEAL_SPLITS: Dict[str, float] = {
    "breakfast": 0.25,
    "lunch": 0.35,
    "dinner": 0.30,
    "snack": 0.10,
}


TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "breakfast": [
        {
            "id": "greek_yogurt_oats",
            "name": "Greek Yogurt Parfait with Berries",
            "description": "Protein-rich Greek yogurt layered with oats, strawberries and almonds.",
            "tags": ["vegetarian", "high-protein"],
            "components": [
                {"food": "greek yogurt", "base_g": 200, "display": "Greek yogurt"},
                {"food": "oats", "base_g": 40, "display": "Rolled oats (dry)"},
                {"food": "strawberry", "base_g": 100, "display": "Fresh strawberries"},
                {"food": "almonds", "base_g": 15, "display": "Sliced almonds"},
            ],
            "instructions": [
                "Spoon the Greek yogurt into a bowl.",
                "Layer in the oats and sliced almonds.",
                "Top with fresh strawberries and serve.",
            ],
            "prep_time": "5 minutes",
        },
        {
            "id": "oatmeal_banana",
            "name": "Banana & Peanut Butter Oatmeal",
            "description": "Classic oats cooked with milk, topped with banana and peanut butter.",
            "tags": ["vegetarian"],
            "components": [
                {"food": "oats", "base_g": 50, "display": "Rolled oats"},
                {"food": "milk", "base_g": 200, "display": "Milk (or plant milk)"},
                {"food": "banana", "base_g": 120, "display": "Banana, sliced"},
                {"food": "peanut butter", "base_g": 16, "display": "Peanut butter"},
            ],
            "instructions": [
                "Simmer oats in milk for 4-5 minutes, stirring often.",
                "Transfer to a bowl.",
                "Top with sliced banana and a spoonful of peanut butter.",
            ],
            "prep_time": "8 minutes",
        },
        {
            "id": "scrambled_eggs_toast",
            "name": "Scrambled Eggs on Whole-Wheat Toast",
            "description": "Soft-scrambled eggs with mashed avocado on whole-grain toast.",
            "tags": ["vegetarian", "high-protein"],
            "components": [
                {"food": "eggs", "base_g": 120, "display": "Eggs (about 2 large)"},
                {"food": "bread whole wheat", "base_g": 60, "display": "Whole-wheat toast"},
                {"food": "avocado", "base_g": 70, "display": "Avocado, mashed"},
                {"food": "olive oil", "base_g": 5, "display": "Olive oil"},
            ],
            "instructions": [
                "Toast two slices of whole-wheat bread.",
                "Whisk the eggs and scramble gently in olive oil over medium-low heat.",
                "Mash the avocado onto the toast and top with the eggs.",
            ],
            "prep_time": "10 minutes",
        },
        {
            "id": "cottage_cheese_bowl",
            "name": "Cottage Cheese & Berry Bowl",
            "description": "High-protein cottage cheese with blueberries, chia seeds and walnuts.",
            "tags": ["vegetarian", "high-protein", "gluten-free"],
            "components": [
                {"food": "cottage cheese", "base_g": 200, "display": "Cottage cheese"},
                {"food": "blueberry", "base_g": 100, "display": "Blueberries"},
                {"food": "chia seeds", "base_g": 10, "display": "Chia seeds"},
                {"food": "walnuts", "base_g": 10, "display": "Walnuts"},
            ],
            "instructions": [
                "Spoon cottage cheese into a bowl.",
                "Top with blueberries, chia seeds and walnuts.",
            ],
            "prep_time": "3 minutes",
        },
    ],
    "lunch": [
        {
            "id": "chicken_quinoa_bowl",
            "name": "Chicken & Quinoa Power Bowl",
            "description": "Grilled chicken over quinoa with broccoli, avocado and olive oil.",
            "tags": ["high-protein", "gluten-free"],
            "components": [
                {"food": "chicken breast", "base_g": 150, "display": "Grilled chicken breast"},
                {"food": "quinoa", "base_g": 150, "display": "Cooked quinoa"},
                {"food": "broccoli", "base_g": 100, "display": "Steamed broccoli"},
                {"food": "avocado", "base_g": 50, "display": "Avocado"},
                {"food": "olive oil", "base_g": 5, "display": "Olive oil drizzle"},
            ],
            "instructions": [
                "Season and grill the chicken breast until cooked through (about 6 minutes per side).",
                "Steam the broccoli until tender-crisp.",
                "Layer the quinoa, broccoli, sliced chicken and avocado in a bowl.",
                "Finish with a drizzle of olive oil.",
            ],
            "prep_time": "20 minutes",
        },
        {
            "id": "tuna_salad",
            "name": "Mediterranean Tuna Salad",
            "description": "Flaked tuna with mixed greens, tomato, cucumber and olive oil.",
            "tags": ["high-protein", "gluten-free"],
            "components": [
                {"food": "tuna", "base_g": 120, "display": "Tuna (canned in water)"},
                {"food": "lettuce", "base_g": 100, "display": "Mixed greens"},
                {"food": "tomato", "base_g": 100, "display": "Cherry tomatoes"},
                {"food": "cucumber", "base_g": 80, "display": "Cucumber, sliced"},
                {"food": "olive oil", "base_g": 10, "display": "Olive oil"},
            ],
            "instructions": [
                "Toss the greens, tomato and cucumber in a bowl.",
                "Top with flaked tuna.",
                "Dress with olive oil, salt and pepper.",
            ],
            "prep_time": "10 minutes",
        },
        {
            "id": "lentil_stew",
            "name": "Hearty Lentil & Vegetable Stew",
            "description": "Warming lentils simmered with carrots, tomato and spinach.",
            "tags": ["vegetarian", "vegan"],
            "components": [
                {"food": "lentils", "base_g": 200, "display": "Cooked lentils"},
                {"food": "carrot", "base_g": 80, "display": "Carrots, diced"},
                {"food": "tomato", "base_g": 100, "display": "Tomatoes, diced"},
                {"food": "spinach", "base_g": 60, "display": "Spinach"},
                {"food": "olive oil", "base_g": 5, "display": "Olive oil"},
            ],
            "instructions": [
                "Sauté the carrots in olive oil until softened.",
                "Add the tomatoes and cooked lentils; simmer for 10 minutes.",
                "Stir in the spinach just before serving.",
            ],
            "prep_time": "25 minutes",
        },
        {
            "id": "chickpea_wrap",
            "name": "Smashed Chickpea & Avocado Wrap",
            "description": "Fibre-rich chickpeas mashed with avocado and greens in a whole-wheat wrap.",
            "tags": ["vegetarian", "vegan"],
            "components": [
                {"food": "chickpeas", "base_g": 150, "display": "Chickpeas"},
                {"food": "avocado", "base_g": 60, "display": "Avocado"},
                {"food": "lettuce", "base_g": 40, "display": "Lettuce"},
                {"food": "bread whole wheat", "base_g": 70, "display": "Whole-wheat wrap"},
            ],
            "instructions": [
                "Mash chickpeas and avocado together with a fork.",
                "Spread on the wrap, add lettuce and roll up.",
                "Slice in half and serve.",
            ],
            "prep_time": "8 minutes",
        },
    ],
    "dinner": [
        {
            "id": "salmon_sweet_potato",
            "name": "Baked Salmon with Sweet Potato & Spinach",
            "description": "Omega-3-rich salmon with roasted sweet potato and sautéed spinach.",
            "tags": ["high-protein", "gluten-free"],
            "components": [
                {"food": "salmon", "base_g": 150, "display": "Salmon fillet"},
                {"food": "sweet potato", "base_g": 200, "display": "Roasted sweet potato"},
                {"food": "spinach", "base_g": 100, "display": "Sautéed spinach"},
                {"food": "olive oil", "base_g": 8, "display": "Olive oil"},
            ],
            "instructions": [
                "Roast sweet potato cubes at 200 °C (400 °F) for 25 minutes.",
                "Bake the salmon with olive oil, salt and pepper for 12 minutes.",
                "Sauté the spinach in olive oil until wilted; plate everything together.",
            ],
            "prep_time": "30 minutes",
        },
        {
            "id": "chicken_stir_fry",
            "name": "Chicken Stir-Fry with Brown Rice",
            "description": "Lean chicken stir-fried with mixed vegetables over brown rice.",
            "tags": ["high-protein"],
            "components": [
                {"food": "chicken breast", "base_g": 150, "display": "Chicken breast"},
                {"food": "rice brown", "base_g": 180, "display": "Cooked brown rice"},
                {"food": "bell pepper", "base_g": 80, "display": "Bell pepper"},
                {"food": "broccoli", "base_g": 100, "display": "Broccoli"},
                {"food": "olive oil", "base_g": 5, "display": "Olive oil"},
            ],
            "instructions": [
                "Slice the chicken and stir-fry in olive oil over high heat.",
                "Add the bell pepper and broccoli; cook until tender-crisp.",
                "Serve over warm brown rice.",
            ],
            "prep_time": "20 minutes",
        },
        {
            "id": "tofu_quinoa",
            "name": "Crispy Tofu with Quinoa & Vegetables",
            "description": "Pan-fried tofu with quinoa, broccoli and carrots.",
            "tags": ["vegetarian", "vegan", "gluten-free"],
            "components": [
                {"food": "tofu", "base_g": 200, "display": "Firm tofu"},
                {"food": "quinoa", "base_g": 150, "display": "Cooked quinoa"},
                {"food": "broccoli", "base_g": 100, "display": "Broccoli"},
                {"food": "carrot", "base_g": 60, "display": "Carrots"},
                {"food": "olive oil", "base_g": 8, "display": "Olive oil"},
            ],
            "instructions": [
                "Press and cube the tofu, then pan-fry in olive oil until golden.",
                "Steam the broccoli and carrots.",
                "Serve tofu and vegetables over quinoa.",
            ],
            "prep_time": "25 minutes",
        },
        {
            "id": "beef_potato",
            "name": "Lean Beef with Roasted Potatoes & Greens",
            "description": "Seared lean beef with roasted potatoes and a spinach side.",
            "tags": ["high-protein", "gluten-free"],
            "components": [
                {"food": "beef lean", "base_g": 140, "display": "Lean beef"},
                {"food": "potato", "base_g": 250, "display": "Roasted potatoes"},
                {"food": "spinach", "base_g": 80, "display": "Spinach"},
                {"food": "olive oil", "base_g": 8, "display": "Olive oil"},
            ],
            "instructions": [
                "Roast potato wedges at 200 °C (400 °F) for 30 minutes.",
                "Sear the beef 3-4 minutes per side; rest for 5 minutes.",
                "Wilt spinach in olive oil and plate together.",
            ],
            "prep_time": "35 minutes",
        },
    ],
    "snack": [
        {
            "id": "apple_pb",
            "name": "Apple Slices with Peanut Butter",
            "description": "Crisp apple served with a spoonful of natural peanut butter.",
            "tags": ["vegetarian", "vegan", "gluten-free"],
            "components": [
                {"food": "apple", "base_g": 180, "display": "Apple"},
                {"food": "peanut butter", "base_g": 16, "display": "Peanut butter"},
            ],
            "instructions": [
                "Slice the apple.",
                "Serve with peanut butter for dipping.",
            ],
            "prep_time": "2 minutes",
        },
        {
            "id": "yogurt_almonds",
            "name": "Greek Yogurt with Almonds",
            "description": "Quick protein-rich snack with yogurt and a handful of almonds.",
            "tags": ["vegetarian", "high-protein", "gluten-free"],
            "components": [
                {"food": "greek yogurt", "base_g": 150, "display": "Greek yogurt"},
                {"food": "almonds", "base_g": 15, "display": "Almonds"},
            ],
            "instructions": [
                "Spoon yogurt into a bowl.",
                "Top with almonds.",
            ],
            "prep_time": "1 minute",
        },
        {
            "id": "hummus_veg",
            "name": "Hummus with Veggie Sticks",
            "description": "Chickpea hummus with crunchy carrots and cucumber.",
            "tags": ["vegetarian", "vegan"],
            "components": [
                {"food": "chickpeas", "base_g": 80, "display": "Chickpeas (blended into hummus)"},
                {"food": "carrot", "base_g": 80, "display": "Carrot sticks"},
                {"food": "cucumber", "base_g": 80, "display": "Cucumber sticks"},
                {"food": "olive oil", "base_g": 5, "display": "Olive oil"},
            ],
            "instructions": [
                "Blend chickpeas with olive oil and a splash of water to make hummus.",
                "Serve with carrot and cucumber sticks.",
            ],
            "prep_time": "5 minutes",
        },
        {
            "id": "banana_walnut",
            "name": "Banana with Walnuts",
            "description": "A quick potassium and omega-3 boost.",
            "tags": ["vegetarian", "vegan", "gluten-free"],
            "components": [
                {"food": "banana", "base_g": 120, "display": "Banana"},
                {"food": "walnuts", "base_g": 15, "display": "Walnuts"},
            ],
            "instructions": [
                "Slice the banana.",
                "Sprinkle with walnuts.",
            ],
            "prep_time": "2 minutes",
        },
    ],
}


# ---------------------------------------------------------------------------
# Filtering logic
# ---------------------------------------------------------------------------

def _normalize(items: Optional[List[str]]) -> List[str]:
    if not items:
        return []
    return [str(x).strip().lower().replace("_", "-") for x in items if x]


def _template_allowed(
    template: Dict[str, Any],
    *,
    dietary: List[str],
    allergies: List[str],
) -> bool:
    tags = {t.lower() for t in template.get("tags", [])}

    if "vegan" in dietary and "vegan" not in tags:
        return False
    if "vegetarian" in dietary and not (tags & {"vegan", "vegetarian"}):
        return False
    if any(d in {"gluten-free", "gluten free"} for d in dietary) and "gluten-free" not in tags:
        return False
    if "dairy-free" in dietary:
        dairy_foods = {"milk", "greek yogurt", "cottage cheese", "yogurt plain",
                       "cheese cheddar", "cheese mozzarella", "butter"}
        if any(comp["food"] in dairy_foods for comp in template["components"]):
            return False

    for comp in template["components"]:
        food_name = comp["food"].lower()
        for allergen in allergies:
            if not allergen:
                continue
            if allergen in food_name:
                return False
            # Simple family matches
            if allergen in {"nuts", "tree nuts"} and any(
                k in food_name for k in ("almond", "walnut", "peanut")
            ):
                return False
            if allergen == "shellfish" and any(k in food_name for k in ("shrimp", "crab")):
                return False

    return True


def _select(
    slot: str,
    *,
    dietary: List[str],
    allergies: List[str],
    seed: int,
) -> Dict[str, Any]:
    candidates = [
        t for t in TEMPLATES[slot]
        if _template_allowed(t, dietary=dietary, allergies=allergies)
    ]
    if not candidates:
        # As a last resort, ignore restrictions so the user still gets a plan.
        candidates = TEMPLATES[slot]
    return candidates[seed % len(candidates)]


def _render_meal(
    template: Dict[str, Any],
    target_calories: float,
    food_db: FoodDatabase,
) -> Dict[str, Any]:
    resolved = []
    base_totals = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    for comp in template["components"]:
        food = food_db.find_food(comp["food"])
        if not food:
            continue
        resolved.append((comp, food))
        grams = comp["base_g"]
        base_totals["calories"] += food["calories"] * grams / 100.0
        base_totals["protein"] += food["protein"] * grams / 100.0
        base_totals["carbs"] += food["carbs"] * grams / 100.0
        base_totals["fat"] += food["fat"] * grams / 100.0

    scale = 1.0
    if base_totals["calories"] > 0:
        scale = max(0.6, min(1.6, target_calories / base_totals["calories"]))

    nutrition = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    ingredients: List[str] = []
    for comp, food in resolved:
        grams = max(1, round(comp["base_g"] * scale))
        nutrition["calories"] += food["calories"] * grams / 100.0
        nutrition["protein"] += food["protein"] * grams / 100.0
        nutrition["carbs"] += food["carbs"] * grams / 100.0
        nutrition["fat"] += food["fat"] * grams / 100.0
        ingredients.append(f"{grams} g {comp['display']}")

    return {
        "name": template["name"],
        "description": template["description"],
        "ingredients": ingredients,
        "instructions": list(template["instructions"]),
        "nutrition": {k: round(v, 1) for k, v in nutrition.items()},
        "prep_time": template["prep_time"],
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def synthesize_daily_plan(
    user_profile: Dict[str, Any],
    seed: int = 0,
) -> Dict[str, Any]:
    """Build a real, portion-scaled daily plan from the local food database."""
    food_db = FoodDatabase()

    target_calories = float(user_profile.get("target_calories") or 2000)
    dietary = _normalize(user_profile.get("dietary_restrictions"))
    allergies = _normalize(user_profile.get("allergies"))

    meals: Dict[str, Any] = {}
    daily_totals = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}

    # Use a slightly different seed per slot so the same day doesn't pick
    # e.g. the "almonds" template for both breakfast and snack.
    for slot_idx, (slot, share) in enumerate(MEAL_SPLITS.items()):
        template = _select(
            slot,
            dietary=dietary,
            allergies=allergies,
            seed=seed + slot_idx * 3,
        )
        meal = _render_meal(template, target_calories * share, food_db)
        meals[slot] = meal
        for k in daily_totals:
            daily_totals[k] += meal["nutrition"][k]

    return {
        "meals": meals,
        "daily_totals": {k: round(v, 1) for k, v in daily_totals.items()},
        "source": "local_food_db",
    }


def synthesize_suggestions(
    user_profile: Dict[str, Any],
    meal_type: str = "any",
    count: int = 5,
) -> List[Dict[str, Any]]:
    """Return up to ``count`` real meal suggestions from the template library."""
    food_db = FoodDatabase()

    target_calories = float(user_profile.get("target_calories") or 2000)
    dietary = _normalize(user_profile.get("dietary_restrictions"))
    allergies = _normalize(user_profile.get("allergies"))

    slots = [meal_type] if meal_type in TEMPLATES else list(TEMPLATES.keys())

    out: List[Dict[str, Any]] = []
    for slot in slots:
        share = MEAL_SPLITS.get(slot, 0.25)
        for template in TEMPLATES[slot]:
            if not _template_allowed(template, dietary=dietary, allergies=allergies):
                continue
            meal = _render_meal(template, target_calories * share, food_db)
            out.append({
                "name": meal["name"],
                "description": meal["description"],
                "meal_type": slot,
                "ingredients": meal["ingredients"],
                "nutrition": meal["nutrition"],
                "prep_time": meal["prep_time"],
                "suitability": (
                    f"Fits a {slot} slot within your ~{int(target_calories)} kcal "
                    f"daily target and respects your dietary preferences."
                ),
            })
            if len(out) >= count:
                return out
    return out


def synthesize_shopping_list(weekly_plan: Dict[str, Any]) -> List[str]:
    """Aggregate weekly ingredients into a categorised shopping list."""
    categories: Dict[str, Dict[str, float]] = {
        "Produce": {},
        "Protein": {},
        "Dairy": {},
        "Grains": {},
        "Pantry": {},
        "Other": {},
    }

    def bucket(name: str) -> str:
        n = name.lower()
        if any(k in n for k in ("chicken", "beef", "pork", "turkey", "salmon", "tuna",
                                 "egg", "tofu", "lentil", "bean", "chickpea")):
            return "Protein"
        if any(k in n for k in ("yogurt", "milk", "cheese", "butter", "cottage")):
            return "Dairy"
        if any(k in n for k in ("rice", "pasta", "bread", "oat", "quinoa", "wrap")):
            return "Grains"
        if any(k in n for k in ("apple", "banana", "berry", "strawberr", "blueberr",
                                 "broccoli", "spinach", "lettuce", "tomato", "carrot",
                                 "onion", "garlic", "pepper", "cucumber", "avocado",
                                 "potato", "orange", "grape")):
            return "Produce"
        if any(k in n for k in ("almond", "walnut", "peanut", "chia", "flax", "oil",
                                 "seed", "honey", "salt", "pepper")):
            return "Pantry"
        return "Other"

    def parse_item(line: str):
        # Ingredients look like "150 g Grilled chicken breast".
        parts = line.split(" ", 2)
        if len(parts) == 3:
            try:
                grams = float(parts[0])
                return parts[2].strip(), grams
            except ValueError:
                pass
        return line.strip(), 0.0

    for day_plan in weekly_plan.values():
        meals = day_plan.get("meals", {})
        for meal in meals.values():
            for ing in meal.get("ingredients", []):
                name, grams = parse_item(ing)
                key = name.lower()
                cat = bucket(name)
                categories[cat][key] = categories[cat].get(key, 0.0) + grams

    shopping_list: List[str] = []
    for cat, items in categories.items():
        if not items:
            continue
        shopping_list.append(f"--- {cat} ---")
        for item, grams in sorted(items.items()):
            shopping_list.append(f"{int(round(grams))} g {item}" if grams else item)
    return shopping_list
