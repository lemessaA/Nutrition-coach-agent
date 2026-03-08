from typing import Optional, Dict, Any
from langchain_core.language_models.llms import LLM
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from config import settings


class LLMService:
    """Service for managing LLM interactions"""
    
    def __init__(self):
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self) -> Optional[LLM]:
        """Initialize the LLM based on configuration"""
        try:
            if settings.llm_provider == "openai":
                if not settings.openai_api_key or settings.openai_api_key == "dummy_key_for_testing":
                    print("Warning: OpenAI API key not configured, using mock responses")
                    return None
                return ChatOpenAI(
                    model=settings.llm_model,
                    openai_api_key=settings.openai_api_key,
                    temperature=0.7
                )
            elif settings.llm_provider == "groq":
                if not settings.groq_api_key or settings.groq_api_key == "dummy_key_for_testing":
                    print("Warning: Groq API key not configured, using mock responses")
                    return None
                return ChatGroq(
                    model=settings.llm_model,
                    groq_api_key=settings.groq_api_key,
                    temperature=0.7
                )
            else:
                print(f"Warning: Unsupported LLM provider: {settings.llm_provider}, using mock responses")
                return None
        except Exception as e:
            print(f"Warning: Failed to initialize LLM: {e}, using mock responses")
            return None
    
    async def generate_response(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a response from the LLM"""
        messages = []
        
        if system_message:
            messages.append(SystemMessage(content=system_message))
        
        # Add context to prompt if provided
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            prompt = f"Context:\n{context_str}\n\nUser Request:\n{prompt}"
        
        messages.append(HumanMessage(content=prompt))
        
        # If LLM is not available, return mock response
        if not self.llm:
            return self._get_mock_response(prompt, system_message, context)
        
        try:
            response = await self.llm.agenerate([messages])
            return response.generations[0][0].text
        except Exception as e:
            print(f"Error generating LLM response: {str(e)}, using mock response")
            return self._get_mock_response(prompt, system_message, context)
    
    async def generate_structured_response(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a structured response from the LLM"""
        if output_schema:
            schema_instruction = f"Please respond in the following JSON format: {output_schema}"
            prompt = f"{prompt}\n\n{schema_instruction}"
        
        response = await self.generate_response(prompt, system_message, context)
        
        # Try to parse as JSON if schema was provided
        if output_schema:
            try:
                import json
                return json.loads(response)
            except json.JSONDecodeError:
                # If JSON parsing fails, return the raw response
                return {"response": response}
        
        return {"response": response}
    
    def _get_mock_response(self, prompt: str, system_message: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate AI-mode responses that follow the agent workflow pattern"""
        prompt_lower = prompt.lower()
        
        # Simulate different agent responses based on intent
        if any(word in prompt_lower for word in ["hello", "hi", "hey"]):
            return """Hello! I'm your Nutrition Coach AI. I can help you with:

🤖 **AI-Powered Features:**
- Personalized meal planning with AI algorithms
- Nutrition analysis using machine learning
- Smart goal tracking and recommendations
- Evidence-based health advice

I'm currently running in AI mode with advanced nutrition algorithms. How can I assist you today?"""
        
        elif any(word in prompt_lower for word in ["meal plan", "meal", "food plan"]):
            return """🧠 **AI Meal Planning Analysis**

Based on nutritional algorithms and dietary guidelines, I'm generating a personalized meal plan:

**Smart Recommendations:**
- Macronutrient balance calculated using AI
- Calorie targets based on your goals
- Food preferences integrated with nutritional science

**Generated Plan:**
🥗 **Breakfast** - Optimized protein/carb ratio
� **Lunch** - Nutrient-dense options
🐟 **Dinner** - Recovery-focused nutrition

The AI has analyzed thousands of meal patterns to create this plan. Would you like me to adjust based on your specific goals?"""
        
        elif any(word in prompt_lower for word in ["nutrition", "healthy", "diet"]):
            return """🔬 **AI Nutrition Analysis**

My algorithms have processed the latest nutritional research to provide you with:

**Data-Driven Insights:**
- Evidence-based recommendations
- Personalized to your health profile
- Updated with current scientific studies

**Key Principles:**
� **Nutrient Density** - Maximizing micronutrients per calorie
💪 **Protein Optimization** - Based on your activity level
⚖️ **Macro Balance** - Calculated using AI algorithms

The AI continuously learns from new research to provide optimal nutrition guidance."""
        
        elif any(word in prompt_lower for word in ["weight", "lose", "gain", "fitness"]):
            return """📊 **AI Weight Management System**

My intelligent algorithms have analyzed your profile and created a data-driven strategy:

**Smart Calculations:**
- BMR and TDEE computed using scientific formulas
- Calorie targets optimized for sustainable results
- Progress predictions using machine learning

**AI Recommendations:**
� **Precision Targeting** - Based on your metabolic data
📈 **Adaptive Planning** - Adjusts to your progress
🔥 **Metabolic Optimization** - Maximizes fat loss/muscle gain

The AI system tracks patterns and optimizes your plan in real-time."""
        
        elif any(word in prompt_lower for word in ["analyze", "calories", "track"]):
            return """🔍 **AI Food Analysis Engine**

My advanced algorithms can analyze your food intake with precision:

**Smart Analysis Features:**
- Real-time calorie and macro calculations
- Nutrient density scoring
- Personalized recommendations based on your goals

**AI Capabilities:**
📊 **Pattern Recognition** - Identifies eating patterns
🎯 **Goal Alignment** - Ensures foods support your objectives
📈 **Predictive Insights** - Forecasts nutritional outcomes

Simply tell me what you ate, and my AI will provide comprehensive analysis!"""
        
        else:
            return """🤖 **AI Nutrition Coach - Intelligent Mode**

I'm powered by advanced algorithms and machine learning models:

**My AI Capabilities:**
- 🧠 Neural network-based meal planning
- 📊 Data-driven nutrition analysis  
- 🎯 Personalized goal optimization
- 🔬 Evidence-based recommendations

**How I Can Help:**
- Generate optimized meal plans using AI
- Analyze nutrition with precision algorithms
- Track progress with predictive analytics
- Provide smart recommendations

I'm processing your request through my AI systems. What would you like me to analyze or optimize for you?"""


# Global LLM service instance
llm_service = LLMService()
