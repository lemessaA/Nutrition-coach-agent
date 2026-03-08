from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from services.llm_service import llm_service


class BaseAgent(ABC):
    """Base class for all nutrition coach agents"""
    
    def __init__(self, name: str):
        self.name = name
        self.llm_service = llm_service
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the input and return a response"""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        pass
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a response using the LLM service"""
        system_message = self.get_system_prompt()
        return await self.llm_service.generate_response(
            prompt=prompt,
            system_message=system_message,
            context=context
        )
    
    async def generate_structured_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a structured response using the LLM service"""
        system_message = self.get_system_prompt()
        return await self.llm_service.generate_structured_response(
            prompt=prompt,
            system_message=system_message,
            context=context,
            output_schema=output_schema
        )
