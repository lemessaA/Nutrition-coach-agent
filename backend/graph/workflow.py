from typing import Dict, Any, List, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import asyncio

from graph.intent_router import IntentRouter
from agents.user_profile_agent import UserProfileAgent
from agents.meal_planner_agent import MealPlannerAgent
from agents.nutrition_knowledge_agent import NutritionKnowledgeAgent
from agents.food_analyzer_agent import FoodAnalyzerAgent
from agents.coaching_agent import CoachingAgent


class NutritionCoachState(TypedDict):
    """State for the nutrition coach workflow"""
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: Optional[str]
    session_id: str
    user_context: Dict[str, Any]
    intent: Optional[str]
    agent_response: Optional[Dict[str, Any]]
    confidence: float
    error: Optional[str]


class NutritionCoachWorkflow:
    """Main workflow coordinator for the Nutrition Coach AI Agent"""
    
    def __init__(self):
        self.intent_router = IntentRouter()
        
        # Initialize agents
        self.agents = {
            "user_profile_agent": UserProfileAgent(),
            "meal_planner_agent": MealPlannerAgent(),
            "nutrition_knowledge_agent": NutritionKnowledgeAgent(),
            "food_analyzer_agent": FoodAnalyzerAgent(),
            "coaching_agent": CoachingAgent(),
        }
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create the graph
        workflow = StateGraph(NutritionCoachState)
        
        # Add nodes
        workflow.add_node("classify_intent", self._classify_intent_node)
        workflow.add_node("route_to_agent", self._route_to_agent_node)
        workflow.add_node("execute_agent", self._execute_agent_node)
        workflow.add_node("format_response", self._format_response_node)
        workflow.add_node("handle_error", self._handle_error_node)
        
        # Add edges
        workflow.set_entry_point("classify_intent")
        workflow.add_edge("classify_intent", "route_to_agent")
        workflow.add_edge("route_to_agent", "execute_agent")
        workflow.add_edge("execute_agent", "format_response")
        workflow.add_edge("format_response", END)
        
        # Add conditional edge for error handling
        workflow.add_conditional_edges(
            "execute_agent",
            self._has_error,
            {
                "error": "handle_error",
                "success": "format_response"
            }
        )
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    async def _classify_intent_node(self, state: NutritionCoachState) -> NutritionCoachState:
        """Classify user intent"""
        try:
            # Get the latest message
            if not state["messages"]:
                state["error"] = "No messages provided"
                return state
            
            latest_message = state["messages"][-1]
            if isinstance(latest_message, HumanMessage):
                user_message = latest_message.content
            else:
                user_message = str(latest_message)
            
            # Classify intent
            classification = await self.intent_router.classify_intent(
                user_message, 
                state.get("user_context", {})
            )
            
            state["intent"] = classification["intent"]
            state["confidence"] = classification["confidence"]
            
            return state
            
        except Exception as e:
            state["error"] = f"Intent classification failed: {str(e)}"
            return state
    
    async def _route_to_agent_node(self, state: NutritionCoachState) -> NutritionCoachState:
        """Route to appropriate agent based on intent"""
        try:
            if not state["messages"]:
                state["error"] = "No messages to route"
                return state
            
            latest_message = state["messages"][-1]
            if isinstance(latest_message, HumanMessage):
                user_message = latest_message.content
            else:
                user_message = str(latest_message)
            
            # Get classification results
            classification = await self.intent_router.classify_intent(
                user_message,
                state.get("user_context", {})
            )
            
            # Route to agent
            routing = await self.intent_router.route_request(classification)
            
            # Store routing info in state
            state["agent_response"] = routing
            
            return state
            
        except Exception as e:
            state["error"] = f"Agent routing failed: {str(e)}"
            return state
    
    async def _execute_agent_node(self, state: NutritionCoachState) -> NutritionCoachState:
        """Execute the selected agent"""
        try:
            if not state.get("agent_response"):
                state["error"] = "No agent routing information"
                return state
            
            routing = state["agent_response"]
            agent_input = routing["agent_input"]
            agent_name = routing["routing"]["agent"]
            
            # Get the agent instance
            if agent_name not in self.agents:
                state["error"] = f"Unknown agent: {agent_name}"
                return state
            
            agent = self.agents[agent_name]
            
            # Execute the agent
            response = await agent.process(agent_input)
            
            # Store response
            state["agent_response"] = {
                "routing": routing["routing"],
                "response": response,
                "agent_name": agent_name
            }
            
            return state
            
        except Exception as e:
            state["error"] = f"Agent execution failed: {str(e)}"
            return state
    
    async def _format_response_node(self, state: NutritionCoachState) -> NutritionCoachState:
        """Format the agent response for the user"""
        try:
            if not state.get("agent_response"):
                state["error"] = "No agent response to format"
                return state
            
            agent_response = state["agent_response"]
            response_data = agent_response["response"]
            
            # Format response based on agent type and success status
            if response_data.get("success"):
                formatted_response = await self._format_success_response(
                    response_data, 
                    agent_response["agent_name"],
                    agent_response["routing"]["intent"]
                )
            else:
                formatted_response = await self._format_error_response(
                    response_data.get("error", "Unknown error"),
                    agent_response["agent_name"]
                )
            
            # Add AI message to state
            ai_message = AIMessage(content=formatted_response)
            state["messages"].append(ai_message)
            
            return state
            
        except Exception as e:
            state["error"] = f"Response formatting failed: {str(e)}"
            return state
    
    async def _handle_error_node(self, state: NutritionCoachState) -> NutritionCoachState:
        """Handle errors in the workflow"""
        error_message = state.get("error", "Unknown error occurred")
        
        # Try to provide a helpful error message
        if "classification" in error_message:
            user_message = "I'm having trouble understanding your request. Could you please rephrase it?"
        elif "routing" in error_message:
            user_message = "I'm not sure how to help with that. Try asking about meal plans, nutrition questions, or food analysis."
        elif "agent" in error_message:
            user_message = "I'm having trouble processing your request right now. Please try again in a moment."
        else:
            user_message = f"Something went wrong: {error_message}. Please try again or contact support."
        
        # Add error message to state
        ai_message = AIMessage(content=user_message)
        state["messages"].append(ai_message)
        
        return state
    
    def _has_error(self, state: NutritionCoachState) -> str:
        """Check if there's an error in the state"""
        return "error" if state.get("error") else "success"
    
    async def _format_success_response(
        self, 
        response_data: Dict[str, Any], 
        agent_name: str, 
        intent: str
    ) -> str:
        """Format successful agent response"""
        
        # Agent-specific formatting
        if agent_name == "meal_planner_agent":
            return await self._format_meal_plan_response(response_data)
        elif agent_name == "nutrition_knowledge_agent":
            return await self._format_nutrition_response(response_data)
        elif agent_name == "food_analyzer_agent":
            return await self._format_food_analysis_response(response_data)
        elif agent_name == "user_profile_agent":
            return await self._format_profile_response(response_data)
        elif agent_name == "coaching_agent":
            return await self._format_coaching_response(response_data)
        else:
            # Default formatting
            return response_data.get("response", "Request completed successfully.")
    
    async def _format_error_response(self, error: str, agent_name: str) -> str:
        """Format error response"""
        error_messages = {
            "user_profile_agent": "I'm having trouble with your profile. Please check your information and try again.",
            "meal_planner_agent": "I can't create a meal plan right now. Please try again later.",
            "nutrition_knowledge_agent": "I'm having trouble finding nutrition information. Please rephrase your question.",
            "food_analyzer_agent": "I can't analyze that food right now. Please try again.",
            "coaching_agent": "I'm having trouble providing coaching support right now. Please try again.",
        }
        
        return error_messages.get(agent_name, f"Error: {error}")
    
    async def _format_meal_plan_response(self, response_data: Dict[str, Any]) -> str:
        """Format meal plan response"""
        if "meal_plan" in response_data:
            meal_plan = response_data["meal_plan"]
            
            # Extract key information
            if "daily_totals" in meal_plan:
                totals = meal_plan["daily_totals"]
                response = f"Here's your meal plan! 🍽️\n\n"
                response += f"**Daily Totals:** {totals.get('calories', 0)} calories, "
                response += f"{totals.get('protein', 0)}g protein, "
                response += f"{totals.get('carbs', 0)}g carbs, {totals.get('fat', 0)}g fat\n\n"
                
                if "meals" in meal_plan:
                    meals = meal_plan["meals"]
                    for meal_name, meal_data in meals.items():
                        response += f"**{meal_name.title()}:** {meal_data.get('name', 'Not specified')}\n"
                        if 'nutrition' in meal_data:
                            nutrition = meal_data['nutrition']
                            response += f"  Calories: {nutrition.get('calories', 0)} | "
                            response += f"Protein: {nutrition.get('protein', 0)}g\n"
                
                return response
        
        return response_data.get("response", "Meal plan created successfully!")
    
    async def _format_nutrition_response(self, response_data: Dict[str, Any]) -> str:
        """Format nutrition knowledge response"""
        answer = response_data.get("answer", "")
        sources = response_data.get("sources", [])
        related_questions = response_data.get("related_questions", [])
        
        response = f"{answer}\n\n"
        
        if sources:
            response += f"**Sources:** {', '.join(sources)}\n\n"
        
        if related_questions:
            response += "**Related questions:**\n"
            for i, q in enumerate(related_questions[:3], 1):
                response += f"{i}. {q}\n"
        
        return response
    
    async def _format_food_analysis_response(self, response_data: Dict[str, Any]) -> str:
        """Format food analysis response"""
        if "analysis" in response_data:
            analysis = response_data["analysis"]
            total_nutrition = analysis.get("total_nutrition", {})
            
            response = f"**Food Analysis Results:** 🥗\n\n"
            response += f"**Calories:** {total_nutrition.get('calories', 0)} kcal\n"
            response += f"**Protein:** {total_nutrition.get('protein', 0)}g\n"
            response += f"**Carbs:** {total_nutrition.get('carbs', 0)}g\n"
            response += f"**Fat:** {total_nutrition.get('fat', 0)}g\n"
            response += f"**Fiber:** {total_nutrition.get('fiber', 0)}g\n\n"
            
            insights = analysis.get("insights", [])
            if insights:
                response += "**Insights:**\n"
                for insight in insights[:3]:
                    response += f"• {insight}\n"
            
            return response
        
        return response_data.get("response", "Food analysis completed!")
    
    async def _format_profile_response(self, response_data: Dict[str, Any]) -> str:
        """Format profile response"""
        if "profile" in response_data:
            profile = response_data["profile"]
            
            response = f"**Profile Updated Successfully!** ✅\n\n"
            response += f"**Target Calories:** {profile.get('target_calories', 0)} kcal/day\n"
            response += f"**Target Protein:** {profile.get('target_protein', 0)}g/day\n"
            response += f"**Target Carbs:** {profile.get('target_carbs', 0)}g/day\n"
            response += f"**Target Fat:** {profile.get('target_fat', 0)}g/day\n\n"
            
            recommendations = response_data.get("recommendations", [])
            if recommendations:
                response += "**Recommendations:**\n"
                for rec in recommendations[:3]:
                    response += f"• {rec}\n"
            
            return response
        
        return response_data.get("response", "Profile updated successfully!")
    
    async def _format_coaching_response(self, response_data: Dict[str, Any]) -> str:
        """Format coaching response"""
        motivation = response_data.get("motivation", "")
        quote = response_data.get("quote", "")
        
        response = ""
        if motivation:
            response += f"{motivation}\n\n"
        
        if quote:
            response += f"💭 *{quote}*"
        
        return response or response_data.get("response", "I'm here to support you!")
    
    async def process_message(
        self, 
        message: str, 
        user_id: Optional[str] = None,
        session_id: str = "default",
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a user message through the workflow"""
        
        # Initialize state
        initial_state = NutritionCoachState(
            messages=[HumanMessage(content=message)],
            user_id=user_id,
            session_id=session_id,
            user_context=user_context or {},
            intent=None,
            agent_response=None,
            confidence=0.0,
            error=None
        )
        
        try:
            # Run the workflow
            result = await self.workflow.ainvoke(initial_state)
            
            # Extract the final AI response
            ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
            
            return {
                "success": True,
                "response": ai_messages[-1].content if ai_messages else "No response generated",
                "session_id": session_id,
                "intent": result.get("intent"),
                "confidence": result.get("confidence"),
                "agent_used": result.get("agent_response", {}).get("agent_name")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Workflow execution failed: {str(e)}",
                "session_id": session_id
            }


# Global workflow instance
nutrition_coach_workflow = NutritionCoachWorkflow()
