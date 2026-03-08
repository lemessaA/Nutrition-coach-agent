from typing import Dict, Any, List
from datetime import datetime, timedelta
import random
from agents.base import BaseAgent


class CoachingAgent(BaseAgent):
    """Agent for providing motivation, habit guidance, and behavioral coaching"""
    
    def __init__(self):
        super().__init__("Coaching Agent")
        self.motivational_quotes = self._load_motivational_quotes()
        self.habit_templates = self._load_habit_templates()
    
    def get_system_prompt(self) -> str:
        return """You are a compassionate and knowledgeable nutrition and wellness coach.
        Your role is to:
        1. Provide motivation and encouragement for health goals
        2. Offer practical habit-building strategies
        3. Help users overcome obstacles and setbacks
        4. Celebrate progress and achievements
        5. Provide accountability and support
        
        Always be empathetic, positive, and realistic in your guidance.
        Focus on small, sustainable changes rather than extreme transformations.
        Acknowledge that health journeys have ups and downs.
        Use evidence-based coaching techniques and behavioral psychology principles."""
    
    def _load_motivational_quotes(self) -> List[str]:
        """Load motivational quotes for nutrition and health"""
        return [
            "Every healthy choice is a victory for your future self.",
            "Progress, not perfection, is the key to lasting change.",
            "Your body is your home - nourish it with love and care.",
            "Small steps daily lead to big changes yearly.",
            "You don't have to be extreme, just consistent.",
            "Nourishing yourself is not selfish, it's essential.",
            "Every meal is an opportunity to fuel your greatness.",
            "Your health is an investment, not an expense.",
            "The journey of a thousand miles begins with a single healthy meal.",
            "You're stronger than any craving or temptation.",
            "Healthy habits are built one day at a time.",
            "Your future self will thank you for the choices you make today.",
            "Transform your body, transform your life.",
            "Wellness is the connection between physical, mental, and social health.",
            "Nourishment comes in many forms - food, movement, rest, and joy."
        ]
    
    def _load_habit_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load habit templates for different goals"""
        return {
            "hydration": [
                {"habit": "Drink a glass of water upon waking", "difficulty": "easy", "impact": "high"},
                {"habit": "Keep a water bottle visible throughout the day", "difficulty": "easy", "impact": "medium"},
                {"habit": "Drink water before each meal", "difficulty": "easy", "impact": "high"},
                {"habit": "Set hourly hydration reminders", "difficulty": "medium", "impact": "medium"},
                {"habit": "Replace one sugary drink with water daily", "difficulty": "medium", "impact": "high"}
            ],
            "balanced_meals": [
                {"habit": "Include protein in every meal", "difficulty": "easy", "impact": "high"},
                {"habit": "Add vegetables to lunch and dinner", "difficulty": "easy", "impact": "high"},
                {"habit": "Practice mindful eating - no screens during meals", "difficulty": "medium", "impact": "high"},
                {"habit": "Prepare healthy snacks in advance", "difficulty": "medium", "impact": "medium"},
                {"habit": "Try one new healthy recipe each week", "difficulty": "medium", "impact": "medium"}
            ],
            "portion_control": [
                {"habit": "Use smaller plates for meals", "difficulty": "easy", "impact": "high"},
                {"habit": "Serve meals in the kitchen, not at the table", "difficulty": "easy", "impact": "medium"},
                {"habit": "Eat slowly and wait 20 minutes before seconds", "difficulty": "medium", "impact": "high"},
                {"habit": "Measure portions for calorie-dense foods", "difficulty": "medium", "impact": "medium"},
                {"habit": "Pre-portion snacks into small containers", "difficulty": "easy", "impact": "high"}
            ],
            "mindful_eating": [
                {"habit": "Take three deep breaths before eating", "difficulty": "easy", "impact": "medium"},
                {"habit": "Chew each bite thoroughly", "difficulty": "easy", "impact": "medium"},
                {"habit": "Put utensils down between bites", "difficulty": "medium", "impact": "medium"},
                {"habit": "Notice flavors and textures of your food", "difficulty": "medium", "impact": "high"},
                {"habit": "Stop eating when you're satisfied, not full", "difficulty": "hard", "impact": "high"}
            ],
            "consistency": [
                {"habit": "Plan meals for the next day", "difficulty": "medium", "impact": "high"},
                {"habit": "Keep a simple food journal", "difficulty": "medium", "impact": "medium"},
                {"habit": "Set a consistent meal schedule", "difficulty": "easy", "impact": "high"},
                {"habit": "Review progress weekly", "difficulty": "easy", "impact": "medium"},
                {"habit": "Prepare for challenging situations in advance", "difficulty": "medium", "impact": "high"}
            ]
        }
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process coaching requests"""
        action = input_data.get("action", "motivate")
        
        if action == "motivate":
            return await self.provide_motivation(input_data)
        elif action == "habit_suggestions":
            return await self.suggest_habits(input_data)
        elif action == "overcome_obstacle":
            return await self.help_overcome_obstacle(input_data)
        elif action == "progress_celebration":
            return await self.celebrate_progress(input_data)
        elif action == "daily_check_in":
            return await self.daily_check_in(input_data)
        elif action == "accountability_reminder":
            return await self.accountability_reminder(input_data)
        else:
            return {"error": f"Unknown action: {action}"}
    
    async def provide_motivation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide personalized motivation"""
        try:
            user_goal = input_data.get("user_goal", "")
            current_challenge = input_data.get("current_challenge", "")
            progress_data = input_data.get("progress_data", {})
            
            # Select relevant motivational quote
            quote = random.choice(self.motivational_quotes)
            
            # Generate personalized motivation
            prompt = f"""
            Provide personalized motivation for someone with the following context:
            
            Goal: {user_goal}
            Current Challenge: {current_challenge}
            Progress: {progress_data}
            
            Include:
            1. Acknowledgment of their efforts
            2. Encouragement specific to their goal
            3. Practical advice for their current challenge
            4. A reminder of their strengths and capabilities
            
            Be warm, encouraging, and specific. Keep it concise but powerful.
            """
            
            motivation = await self.generate_response(prompt)
            
            return {
                "success": True,
                "motivation": motivation,
                "quote": quote,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Error providing motivation: {str(e)}"}
    
    async def suggest_habits(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest personalized habits based on goals and preferences"""
        try:
            user_goal = input_data.get("user_goal", "")
            current_habits = input_data.get("current_habits", [])
            preferences = input_data.get("preferences", {})
            difficulty_level = input_data.get("difficulty_level", "easy")
            
            # Select relevant habit categories based on goal
            relevant_categories = self._get_relevant_habit_categories(user_goal)
            
            suggested_habits = []
            for category in relevant_categories:
                habits = self.habit_templates.get(category, [])
                
                # Filter by difficulty and exclude current habits
                filtered_habits = [
                    habit for habit in habits 
                    if habit["difficulty"] == difficulty_level or difficulty_level == "all"
                    if habit["habit"] not in current_habits
                ]
                
                suggested_habits.extend(filtered_habits[:2])  # Top 2 from each category
            
            # Generate personalized advice
            prompt = f"""
            Provide advice on building healthy habits for someone with these details:
            
            Goal: {user_goal}
            Current habits: {current_habits}
            Preferences: {preferences}
            Difficulty preference: {difficulty_level}
            
            Suggested habits: {[habit['habit'] for habit in suggested_habits[:3]]}
            
            Provide:
            1. Why these habits are particularly relevant to their goal
            2. How to implement them successfully
            3. How to track progress
            4. What to expect in the first few weeks
            """
            
            advice = await self.generate_response(prompt)
            
            return {
                "success": True,
                "suggested_habits": suggested_habits[:5],  # Top 5 suggestions
                "implementation_advice": advice,
                "categories_covered": relevant_categories,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Error suggesting habits: {str(e)}"}
    
    async def help_overcome_obstacle(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Help users overcome specific obstacles"""
        try:
            obstacle_type = input_data.get("obstacle_type", "")
            obstacle_description = input_data.get("obstacle_description", "")
            user_context = input_data.get("user_context", {})
            
            # Generate targeted advice
            prompt = f"""
            Provide practical strategies to overcome this obstacle:
            
            Obstacle Type: {obstacle_type}
            Description: {obstacle_description}
            User Context: {user_context}
            
            Provide:
            1. Immediate coping strategies
            2. Long-term prevention tactics
            3. Mindset shifts to help
            4. When to seek additional support
            5. A specific action plan for the next week
            
            Be empathetic, practical, and solution-focused.
            """
            
            strategies = await self.generate_response(prompt)
            
            # Generate specific action plan
            action_plan = await self._generate_action_plan(obstacle_type, obstacle_description)
            
            return {
                "success": True,
                "obstacle_type": obstacle_type,
                "strategies": strategies,
                "action_plan": action_plan,
                "follow_up_needed": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Error helping overcome obstacle: {str(e)}"}
    
    async def celebrate_progress(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Celebrate user progress and achievements"""
        try:
            achievements = input_data.get("achievements", [])
            time_period = input_data.get("time_period", "week")
            user_goal = input_data.get("user_goal", "")
            
            # Generate celebration message
            prompt = f"""
            Create an uplifting celebration message for someone who has achieved:
            
            Achievements: {achievements}
            Time Period: {time_period}
            Goal: {user_goal}
            
            Include:
            1. Genuine acknowledgment of their hard work
            2. How these achievements contribute to their bigger goal
            3. The positive impact on their health and wellbeing
            4. Encouragement for continued progress
            5. Ideas for celebrating in healthy ways
            
            Be enthusiastic, specific, and motivating.
            """
            
            celebration = await self.generate_response(prompt)
            
            # Suggest healthy celebration ideas
            celebration_ideas = [
                "Try a new healthy recipe you've been curious about",
                "Go for a nature walk or hike in a beautiful place",
                "Schedule a massage or spa treatment",
                "Buy a new workout outfit or kitchen gadget",
                "Have a dance party with your favorite music",
                "Take progress photos to see how far you've come",
                "Share your success with supportive friends or family",
                "Try a new fitness class or activity"
            ]
            
            return {
                "success": True,
                "celebration_message": celebration,
                "celebration_ideas": random.sample(celebration_ideas, 3),
                "achievements_count": len(achievements),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Error celebrating progress: {str(e)}"}
    
    async def daily_check_in(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide daily check-in support"""
        try:
            day_number = input_data.get("day_number", 1)
            mood = input_data.get("mood", "")
            challenges = input_data.get("challenges", [])
            wins = input_data.get("wins", [])
            user_goal = input_data.get("user_goal", "")
            
            # Generate personalized check-in response
            prompt = f"""
            Provide a supportive daily check-in response for:
            
            Day {day_number} of their health journey
            Current mood: {mood}
            Today's challenges: {challenges}
            Today's wins: {wins}
            Goal: {user_goal}
            
            Include:
            1. Acknowledgment of their mood and experiences
            2. Celebration of their wins, no matter how small
            3. Support for their challenges
            4. A focus for tomorrow
            5. A reminder of their 'why'
            
            Be warm, personal, and encouraging.
            """
            
            check_in_response = await self.generate_response(prompt)
            
            # Suggest tomorrow's focus
            tomorrow_focus = await self._suggest_tomorrow_focus(challenges, wins, user_goal)
            
            return {
                "success": True,
                "check_in_response": check_in_response,
                "tomorrow_focus": tomorrow_focus,
                "day_number": day_number,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Error in daily check-in: {str(e)}"}
    
    async def accountability_reminder(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide accountability reminders"""
        try:
            commitment = input_data.get("commitment", "")
            reminder_type = input_data.get("reminder_type", "daily")
            user_name = input_data.get("user_name", "there")
            
            # Generate accountability message
            prompt = f"""
            Create an accountability reminder for:
            
            User: {user_name}
            Commitment: {commitment}
            Reminder Type: {reminder_type}
            
            Include:
            1. A gentle but firm reminder of their commitment
            2. Why this matters to their goals
            3. A specific action they can take right now
            4. Encouragement that they can do this
            5. A reminder of past successes
            
            Be supportive, motivating, and action-oriented.
            """
            
            reminder = await self.generate_response(prompt)
            
            return {
                "success": True,
                "reminder_message": reminder,
                "commitment": commitment,
                "reminder_type": reminder_type,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Error creating accountability reminder: {str(e)}"}
    
    def _get_relevant_habit_categories(self, user_goal: str) -> List[str]:
        """Get relevant habit categories based on user goal"""
        goal_mapping = {
            "lose_weight": ["hydration", "portion_control", "balanced_meals", "mindful_eating"],
            "gain_muscle": ["balanced_meals", "consistency", "hydration"],
            "maintain_health": ["hydration", "balanced_meals", "mindful_eating", "consistency"],
            "eat_healthier": ["balanced_meals", "hydration", "mindful_eating"],
            "be_more_active": ["consistency", "hydration"],
            "reduce_stress": ["mindful_eating", "hydration", "consistency"]
        }
        
        return goal_mapping.get(user_goal, ["hydration", "balanced_meals", "consistency"])
    
    async def _generate_action_plan(self, obstacle_type: str, obstacle_description: str) -> List[str]:
        """Generate a specific action plan for overcoming obstacles"""
        prompt = f"""
        Create a 7-day action plan to overcome: {obstacle_type}
        Description: {obstacle_description}
        
        Provide 7 specific, actionable steps - one for each day.
        Each step should be small, achievable, and build on previous days.
        Format as a numbered list.
        """
        
        response = await self.generate_response(prompt)
        # Parse response into list
        action_steps = [step.strip() for step in response.split('\n') if step.strip() and any(char.isdigit() for char in step)]
        return action_steps[:7]
    
    async def _suggest_tomorrow_focus(self, challenges: List[str], wins: List[str], user_goal: str) -> str:
        """Suggest a focus area for tomorrow based on today's experiences"""
        prompt = f"""
        Based on today's experiences, suggest one specific focus for tomorrow:
        
        Challenges faced: {challenges}
        Wins achieved: {wins}
            Goal: {user_goal}
        
        Suggest ONE specific, achievable focus area for tomorrow that builds on today's experiences.
        Make it concrete and actionable.
        """
        
        return await self.generate_response(prompt)