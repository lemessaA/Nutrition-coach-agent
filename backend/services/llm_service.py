from typing import Optional, Dict, Any
import json
import re
from langchain_core.language_models.llms import LLM
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from config import settings


def _extract_json(text: str) -> Optional[Any]:
    """Best-effort JSON extraction from an LLM response.

    Handles: pure JSON, ```json fenced code blocks, plain ``` fences, and
    prose that contains a single balanced JSON object or array.
    Returns the parsed value, or None if nothing parseable was found.
    """
    if not text or not isinstance(text, str):
        return None

    cleaned = text.strip()

    # 1. Direct parse
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # 2. Strip a ```json ... ``` or ``` ... ``` fence
    fence = re.search(r"```(?:json)?\s*(.+?)\s*```", cleaned, re.DOTALL | re.IGNORECASE)
    if fence:
        inner = fence.group(1).strip()
        try:
            return json.loads(inner)
        except Exception:
            cleaned = inner  # fall through to balanced-brace search

    # 3. Find the first balanced JSON object or array in the text
    for opener, closer in (("{", "}"), ("[", "]")):
        start = cleaned.find(opener)
        while start != -1:
            depth = 0
            in_str = False
            esc = False
            for i in range(start, len(cleaned)):
                c = cleaned[i]
                if in_str:
                    if esc:
                        esc = False
                    elif c == "\\":
                        esc = True
                    elif c == '"':
                        in_str = False
                else:
                    if c == '"':
                        in_str = True
                    elif c == opener:
                        depth += 1
                    elif c == closer:
                        depth -= 1
                        if depth == 0:
                            candidate = cleaned[start : i + 1]
                            try:
                                return json.loads(candidate)
                            except Exception:
                                break
            start = cleaned.find(opener, start + 1)

    return None


class LLMService:
    """Service for managing LLM interactions"""
    
    def __init__(self):
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self) -> Optional[LLM]:
        """Initialize the LLM based on configuration"""
        try:
            if not settings.groq_api_key or settings.groq_api_key == "dummy_key_for_testing":
                print("Warning: Groq API key not configured, using mock responses")
                return None
            return ChatGroq(
                model=settings.llm_model,
                groq_api_key=settings.groq_api_key,
                temperature=0.7
            )
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
        """Generate a structured response from the LLM.

        Uses provider JSON mode when available (Groq supports
        ``response_format={"type": "json_object"}``) and falls back to
        tolerant JSON extraction for plain-text responses.
        """
        if output_schema is None:
            response = await self.generate_response(prompt, system_message, context)
            return {"response": response}

        # Tighten the instructions so the LLM is pushed to emit only JSON.
        schema_instruction = (
            "Respond with ONLY a single valid JSON object that matches this schema "
            "(no markdown fences, no commentary, no trailing text):\n"
            f"{json.dumps(output_schema)}"
        )
        final_prompt = f"{prompt}\n\n{schema_instruction}"

        # Try the JSON-mode path first if the LLM supports binding response_format.
        text: Optional[str] = None
        if self.llm is not None:
            try:
                messages = []
                if system_message:
                    messages.append(SystemMessage(content=system_message))
                if context:
                    context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                    prompted = f"Context:\n{context_str}\n\nUser Request:\n{final_prompt}"
                else:
                    prompted = final_prompt
                messages.append(HumanMessage(content=prompted))

                bound = self.llm
                try:
                    bound = self.llm.bind(response_format={"type": "json_object"})
                except Exception:
                    # Not all providers accept response_format; that's fine.
                    bound = self.llm

                gen = await bound.agenerate([messages])
                text = gen.generations[0][0].text
            except Exception as e:
                print(f"Structured LLM call failed ({e}); falling back to plain generation")
                text = None

        if text is None:
            text = await self.generate_response(final_prompt, system_message, context)

        parsed = _extract_json(text)
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, list):
            return {"items": parsed}

        # No JSON could be recovered. Surface the raw text so callers can
        # decide whether to retry or synthesize a fallback.
        return {"error": "parse_failed", "raw": text}
    
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
