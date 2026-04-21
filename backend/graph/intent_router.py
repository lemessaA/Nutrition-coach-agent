from typing import Dict, Any, List, Optional
import re
from langchain_core.messages import HumanMessage, SystemMessage
from services.llm_service import llm_service


class IntentRouter:
    """Routes user requests to appropriate agents based on intent classification"""
    
    def __init__(self):
        self.intent_patterns = self._initialize_intent_patterns()
        self.agent_mapping = self._initialize_agent_mapping()
    
    def _initialize_intent_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for intent recognition"""
        return {
            "profile_management": [
                r"update\s+(my\s+)?profile",
                r"change\s+(my\s+)?(profile|information)",
                r"set\s+(my\s+)?(goals?|targets?)",
                r"personal\s+information",
                r"health\s+profile",
                r"body\s+stats?",
                r"weight\s+(and\s+)?height",
                r"activity\s+level"
            ],
            "meal_planning": [
                r"meal\s+plan",
                r"create\s+(a\s+)?(meal\s+)?plan",
                r"daily\s+meals?",
                r"weekly\s+meals?",
                r"what\s+should\s+i\s+eat",
                r"meal\s+suggestions?",
                r"food\s+plan",
                r"nutrition\s+plan",
                r"diet\s+plan",
                r"recipe\s+suggestions?"
            ],
            "nutrition_knowledge": [
                r"how\s+much\s+(protein|carbs|fat|calories)",
                r"is\s+.+\s+(healthy|good|bad)",
                r"what\s+is\s+(a\s+)?(healthy|good)",
                r"nutrition\s+(question|advice|info)",
                r"tell\s+me\s+about",
                r"explain\s+.+",
                r"why\s+is\s+.+",
                r"benefits?\s+of",
                r"vitamin\s+\w+",
                r"mineral\s+\w+"
            ],
            "food_analysis": [
                r"analyze\s+(this\s+)?food",
                r"calories\s+in",
                r"nutrition\s+in",
                r"how\s+many\s+calories",
                r"macro\s+(count|nutrients?|breakdown)",
                r"food\s+analysis",
                r"track\s+(this\s+)?meal",
                r"log\s+(this\s+)?food",
                r"nutrition\s+facts?"
            ],
            "coaching": [
                r"motivate\s+me",
                r"help\s+me\s+stay\s+on\s+track",
                r"struggling\s+with",
                r"can't\s+stay\s+motivated",
                r"need\s+(encouragement|support)",
                r"habit\s+(help|advice)",
                r"overcome\s+(obstacle|challenge)",
                r"celebrate\s+(progress|success)",
                r"daily\s+check.?in"
            ],
            "general_chat": [
                r"hello",
                r"hi",
                r"hey",
                r"how\s+are\s+you",
                r"what\s+can\s+you\s+do",
                r"help",
                r"assist",
                r"support"
            ]
        }
    
    def _initialize_agent_mapping(self) -> Dict[str, str]:
        """Map intents to agent names"""
        return {
            "profile_management": "user_profile_agent",
            "meal_planning": "meal_planner_agent",
            "nutrition_knowledge": "nutrition_knowledge_agent",
            "food_analysis": "food_analyzer_agent",
            "coaching": "coaching_agent",
            "general_chat": "coaching_agent"  # Default to coaching for general chat
        }
    
    async def classify_intent(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Classify user intent using pattern matching and LLM"""
        
        # Pattern-based classification first
        pattern_intent = self._classify_by_patterns(message)
        
        if pattern_intent:
            confidence = 0.8  # High confidence for pattern matches
        else:
            # Use LLM for classification
            llm_result = await self._classify_with_llm(message, context)
            pattern_intent = llm_result["intent"]
            confidence = llm_result["confidence"]
        
        # Map intent to agent
        agent_name = self.agent_mapping.get(pattern_intent, "coaching_agent")
        
        return {
            "intent": pattern_intent,
            "agent": agent_name,
            "confidence": confidence,
            "message": message,
            "context": context or {}
        }
    
    def _classify_by_patterns(self, message: str) -> Optional[str]:
        """Classify intent using regex patterns"""
        message_lower = message.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent
        
        return None
    
    async def _classify_with_llm(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Use LLM to classify intent when patterns don't match"""
        
        system_prompt = """You are an intent classification expert for a nutrition coaching AI.
        
        Classify the user's message into one of these categories:
        - profile_management: User wants to update or manage their health profile
        - meal_planning: User wants meal plans, recipes, or food suggestions
        - nutrition_knowledge: User asks nutrition questions or wants information
        - food_analysis: User wants to analyze food for calories/macros
        - coaching: User needs motivation, habit help, or emotional support
        - general_chat: General conversation, greetings, or help requests
        
        Respond with JSON format: {"intent": "category", "confidence": 0.0, "reasoning": "explanation"}
        """
        
        context_str = ""
        if context:
            context_str = f"Context: {context}\n\n"
        
        prompt = f"{context_str}User message: {message}"
        
        try:
            response = await llm_service.generate_response(
                prompt=prompt,
                system_message=system_prompt
            )
            
            # Parse JSON response
            import json
            result = json.loads(response)
            
            # Validate intent
            if result.get("intent") not in self.agent_mapping:
                result["intent"] = "general_chat"
                result["confidence"] = 0.5
            
            return result
            
        except Exception as e:
            # Fallback to general chat
            return {
                "intent": "general_chat",
                "confidence": 0.3,
                "reasoning": f"Classification error: {str(e)}"
            }
    
    async def route_request(self, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Route the request to the appropriate agent"""
        
        intent = classification["intent"]
        agent_name = classification["agent"]
        message = classification["message"]
        context = classification["context"]
        
        # Prepare agent-specific input
        agent_input = await self._prepare_agent_input(intent, message, context)
        
        return {
            "routing": {
                "intent": intent,
                "agent": agent_name,
                "confidence": classification["confidence"]
            },
            "agent_input": agent_input
        }
    
    async def _prepare_agent_input(self, intent: str, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare input specific to each agent type"""
        
        base_input = {
            "message": message,
            "context": context,
            "original_intent": intent
        }
        
        # Add intent-specific parameters
        if intent == "profile_management":
            base_input["action"] = "update" if "update" in message.lower() else "create"
            base_input.update(context)
        
        elif intent == "meal_planning":
            base_input["action"] = "generate"
            base_input["plan_type"] = "daily" if "daily" in message.lower() else "weekly"
            base_input["user_profile"] = context.get("user_profile", {})
        
        elif intent == "nutrition_knowledge":
            base_input["action"] = "answer"
            base_input["question"] = message
            base_input["user_profile"] = context.get("user_profile", {})
        
        elif intent == "food_analysis":
            base_input["action"] = "analyze"
            base_input["food_input"] = message
            base_input["user_profile"] = context.get("user_profile", {})
        
        elif intent == "coaching":
            if "motivate" in message.lower():
                base_input["action"] = "motivate"
            elif "habit" in message.lower():
                base_input["action"] = "habit_suggestions"
            elif "struggling" in message.lower() or "challenge" in message.lower():
                base_input["action"] = "overcome_obstacle"
            else:
                base_input["action"] = "daily_check_in"
            
            base_input["user_goal"] = context.get("user_profile", {}).get("goal")
        
        elif intent == "general_chat":
            base_input["action"] = "motivate"  # Default to coaching response
        
        return base_input
    
    def _extract_food_items(self, message: str) -> List[str]:
        """Extract food items from message"""
        # Simple extraction - in real implementation would be more sophisticated
        food_keywords = [
            "chicken", "beef", "fish", "salmon", "eggs", "milk", "cheese",
            "bread", "rice", "pasta", "potatoes", "vegetables", "fruits",
            "apples", "bananas", "tomatoes", "onions", "garlic"
        ]
        
        message_lower = message.lower()
        found_items = []
        
        for food in food_keywords:
            if food in message_lower:
                found_items.append(food)
        
        return found_items
    
    async def get_fallback_response(self, message: str) -> str:
        """Get fallback response when classification fails"""
        fallback_responses = [
            "I'm not sure I understand. Could you tell me more about what you need help with?",
            "I can help with meal planning, nutrition questions, food analysis, and coaching. What would you like to know?",
            "Let me help you better. Are you looking for meal ideas, nutrition information, or something else?",
            "I'm here to help with your nutrition journey. Try asking me about meal plans, healthy recipes, or nutrition facts!"
        ]
        
        import random
        return random.choice(fallback_responses)
