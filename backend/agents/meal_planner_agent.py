from typing import Dict, Any, List
from datetime import datetime

from agents.base import BaseAgent
from services.meal_synthesizer import (
    synthesize_daily_plan,
    synthesize_suggestions,
    synthesize_shopping_list,
)


DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


class MealPlannerAgent(BaseAgent):
    """Agent for generating personalized meal plans.

    The agent first asks the LLM for a structured plan in JSON mode.  If the
    LLM is unavailable or produces an unparseable/incomplete response, it falls
    back to :mod:`services.meal_synthesizer`, which builds a real plan from the
    local food-nutrition database with portions scaled to the user's targets.
    """

    def __init__(self) -> None:
        super().__init__("Meal Planner Agent")

    def get_system_prompt(self) -> str:
        return (
            "You are a professional meal planning and nutrition expert. "
            "Create balanced, realistic plans that hit the user's calorie and macro "
            "targets, respect their dietary restrictions and allergies, and use "
            "whole foods where possible. When asked for JSON, respond with ONLY a "
            "single JSON object — no markdown fences, no commentary."
        )

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        action = input_data.get("action", "generate")

        if action == "generate":
            return await self.generate_meal_plan(input_data)
        if action == "daily":
            return await self.generate_daily_plan(input_data)
        if action == "weekly":
            return await self.generate_weekly_plan(input_data)
        if action == "meal_suggestions":
            return await self.get_meal_suggestions(input_data)
        return {"error": f"Unknown action: {action}"}

    async def generate_meal_plan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            user_profile = input_data.get("user_profile")
            plan_type = input_data.get("plan_type", "daily")

            if not user_profile:
                return {"error": "User profile is required for meal planning"}

            if plan_type == "daily":
                return await self.generate_daily_plan(input_data)
            if plan_type == "weekly":
                return await self.generate_weekly_plan(input_data)
            return {"error": f"Unsupported plan type: {plan_type}"}
        except Exception as e:  # pragma: no cover - defensive
            return {"error": f"Error generating meal plan: {str(e)}"}

    # ------------------------------------------------------------------
    # Daily plan
    # ------------------------------------------------------------------
    async def generate_daily_plan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            user_profile = input_data.get("user_profile") or {}
            preferences = input_data.get("preferences", {}) or {}
            day_seed = int(
                preferences.get("day_seed")
                or input_data.get("day_seed")
                or 0
            )

            target_calories = user_profile.get("target_calories", 2000)
            target_protein = user_profile.get("target_protein", 150)
            target_carbs = user_profile.get("target_carbs", 250)
            target_fat = user_profile.get("target_fat", 65)

            dietary_restrictions = user_profile.get("dietary_restrictions") or []
            allergies = user_profile.get("allergies") or []
            preferences_list = user_profile.get("preferences") or []

            prompt = f"""
            Create a detailed one-day meal plan for a real person with these targets:

            TARGETS (must be respected within ~10%):
            - Calories: {target_calories} kcal
            - Protein: {target_protein} g
            - Carbs: {target_carbs} g
            - Fat: {target_fat} g

            USER PROFILE:
            - Goal: {user_profile.get('goal', 'general health')}
            - Activity level: {user_profile.get('activity_level', 'moderate')}
            - Dietary restrictions: {dietary_restrictions or 'None'}
            - Allergies: {allergies or 'None'}
            - Preferences: {preferences_list or 'None'}
            - Day hint: {preferences.get('day', 'today')}

            Produce four meals with this calorie split:
            - Breakfast: 25% of daily calories
            - Lunch: 35%
            - Dinner: 30%
            - Snack: 10%

            For each meal include: name, description, ingredients with quantities in
            grams or common units, step-by-step instructions, per-meal nutrition
            (calories, protein, carbs, fat), and prep_time.
            """

            schema = {
                "meals": {
                    "breakfast": {
                        "name": "string",
                        "description": "string",
                        "ingredients": ["string"],
                        "instructions": ["string"],
                        "nutrition": {
                            "calories": "number",
                            "protein": "number",
                            "carbs": "number",
                            "fat": "number",
                        },
                        "prep_time": "string",
                    },
                    "lunch": "same shape as breakfast",
                    "dinner": "same shape as breakfast",
                    "snack": "same shape as breakfast",
                },
                "daily_totals": {
                    "calories": "number",
                    "protein": "number",
                    "carbs": "number",
                    "fat": "number",
                },
            }

            response = await self.generate_structured_response(
                prompt=prompt,
                output_schema=schema,
            )

            meal_plan = self._coerce_meal_plan(response)
            if meal_plan is None:
                # LLM unavailable or returned something unusable -> build a real
                # plan from the local food database.
                synthesized = synthesize_daily_plan(user_profile, seed=day_seed)
                return {
                    "success": True,
                    "meal_plan": synthesized,
                    "plan_type": "daily",
                    "created_date": datetime.now().isoformat(),
                    "source": "local_food_db",
                }

            # Ensure daily_totals exist even if the LLM forgot them.
            meal_plan.setdefault("daily_totals", self._sum_totals(meal_plan["meals"]))

            daily_totals = meal_plan.get("daily_totals", {})
            tolerance = target_calories * 0.15
            if abs(daily_totals.get("calories", 0) - target_calories) > tolerance:
                meal_plan["note"] = (
                    "Calorie total deviates from target by more than 15%; "
                    "consider regenerating or scaling portions."
                )

            return {
                "success": True,
                "meal_plan": meal_plan,
                "plan_type": "daily",
                "created_date": datetime.now().isoformat(),
                "source": "llm",
            }
        except Exception as e:
            # Never throw an error back to the user — synthesize a real plan.
            try:
                synthesized = synthesize_daily_plan(
                    input_data.get("user_profile") or {},
                    seed=0,
                )
                return {
                    "success": True,
                    "meal_plan": synthesized,
                    "plan_type": "daily",
                    "created_date": datetime.now().isoformat(),
                    "source": "local_food_db",
                    "warning": f"LLM path failed: {e}",
                }
            except Exception as inner:
                return {"error": f"Error generating daily meal plan: {inner}"}

    # ------------------------------------------------------------------
    # Weekly plan
    # ------------------------------------------------------------------
    async def generate_weekly_plan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            user_profile = input_data.get("user_profile") or {}
            if not user_profile:
                return {"error": "User profile is required for meal planning"}

            weekly_plan: Dict[str, Any] = {}
            used_llm = False

            for idx, day in enumerate(DAY_NAMES):
                daily_input = dict(input_data)
                prefs = dict(input_data.get("preferences") or {})
                prefs["day"] = day
                prefs["day_seed"] = idx
                daily_input["preferences"] = prefs
                daily_input["day_seed"] = idx

                daily = await self.generate_daily_plan(daily_input)
                if "error" in daily:
                    # Still emit a synthesized day rather than failing the week.
                    synthesized = synthesize_daily_plan(user_profile, seed=idx)
                    weekly_plan[day.lower()] = synthesized
                    continue

                weekly_plan[day.lower()] = daily["meal_plan"]
                if daily.get("source") == "llm":
                    used_llm = True

            return {
                "success": True,
                "meal_plan": weekly_plan,
                "plan_type": "weekly",
                "created_date": datetime.now().isoformat(),
                "shopping_list": synthesize_shopping_list(weekly_plan),
                "source": "llm" if used_llm else "local_food_db",
            }
        except Exception as e:
            return {"error": f"Error generating weekly meal plan: {str(e)}"}

    # ------------------------------------------------------------------
    # Meal suggestions
    # ------------------------------------------------------------------
    async def get_meal_suggestions(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            meal_type = input_data.get("meal_type", "any")
            user_profile = input_data.get("user_profile") or {}

            prompt = f"""
            Suggest 5 diverse meal ideas for {meal_type} that fit this profile:

            - Goal: {user_profile.get('goal', 'general health')}
            - Dietary restrictions: {user_profile.get('dietary_restrictions') or 'None'}
            - Allergies: {user_profile.get('allergies') or 'None'}
            - Preferences: {user_profile.get('preferences') or 'None'}

            For each suggestion include: name, description, ingredients (with grams
            or units), approximate per-serving nutrition, and a one-line
            explanation of why it fits the user's goals.
            """

            schema = {
                "suggestions": [
                    {
                        "name": "string",
                        "description": "string",
                        "ingredients": ["string"],
                        "nutrition": {
                            "calories": "number",
                            "protein": "number",
                            "carbs": "number",
                            "fat": "number",
                        },
                        "suitability": "string",
                    }
                ]
            }

            response = await self.generate_structured_response(
                prompt=prompt,
                output_schema=schema,
            )

            suggestions: List[Dict[str, Any]] = []
            if isinstance(response, dict):
                raw = response.get("suggestions") or response.get("items")
                if isinstance(raw, list):
                    suggestions = [s for s in raw if isinstance(s, dict) and s.get("name")]

            source = "llm"
            if not suggestions:
                suggestions = synthesize_suggestions(user_profile, meal_type=meal_type)
                source = "local_food_db"

            return {
                "success": True,
                "meal_type": meal_type,
                "suggestions": suggestions,
                "source": source,
            }
        except Exception as e:
            try:
                return {
                    "success": True,
                    "meal_type": input_data.get("meal_type", "any"),
                    "suggestions": synthesize_suggestions(
                        input_data.get("user_profile") or {},
                        meal_type=input_data.get("meal_type", "any"),
                    ),
                    "source": "local_food_db",
                    "warning": f"LLM path failed: {e}",
                }
            except Exception as inner:
                return {"error": f"Error getting meal suggestions: {inner}"}

    async def generate_shopping_list(self, weekly_plan: Dict[str, Any]) -> List[str]:
        """Back-compat helper delegating to the synthesizer."""
        return synthesize_shopping_list(weekly_plan)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _coerce_meal_plan(response: Any) -> Any:
        """Extract a usable meal plan from the LLM response.

        Returns ``None`` if the response can't be used and the caller should
        fall back to the synthesizer.
        """
        if not isinstance(response, dict):
            return None
        if response.get("error") == "parse_failed":
            return None
        # Allow the LLM to return either {"meal_plan": {...}} or the bare shape.
        candidate = response.get("meal_plan") if "meal_plan" in response else response
        if not isinstance(candidate, dict):
            return None
        meals = candidate.get("meals")
        if not isinstance(meals, dict):
            return None
        required = {"breakfast", "lunch", "dinner", "snack"}
        if not required.issubset(meals.keys()):
            return None
        for slot in required:
            m = meals[slot]
            if not isinstance(m, dict) or "nutrition" not in m:
                return None
        return candidate

    @staticmethod
    def _sum_totals(meals: Dict[str, Any]) -> Dict[str, float]:
        totals = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
        for meal in meals.values():
            nutrition = meal.get("nutrition", {}) if isinstance(meal, dict) else {}
            for k in totals:
                try:
                    totals[k] += float(nutrition.get(k, 0) or 0)
                except (TypeError, ValueError):
                    continue
        return {k: round(v, 1) for k, v in totals.items()}
