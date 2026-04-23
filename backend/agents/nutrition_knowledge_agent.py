from typing import Dict, Any, List
from agents.base import BaseAgent
from rag.vector_store import vector_store
from rag.knowledge_base import knowledge_base
from langchain_core.documents import Document


class NutritionKnowledgeAgent(BaseAgent):
    """Agent for answering nutrition questions using RAG (Retrieval-Augmented Generation)"""
    
    def __init__(self):
        super().__init__("Nutrition Knowledge Agent")
        self.initialize_knowledge_base()
    
    def get_system_prompt(self) -> str:
        return """You are a certified nutritionist and dietitian with extensive knowledge of nutrition science.
        Your role is to:
        1. Answer nutrition questions accurately based on scientific evidence
        2. Use the provided knowledge base and context to inform your answers
        3. Provide practical, actionable advice
        4. Acknowledge when information is not available and suggest consulting healthcare providers
        5. Consider individual differences and avoid one-size-fits-all recommendations
        
        Always cite your sources when possible and distinguish between established facts and general recommendations.
        Be encouraging and non-judgmental in your responses."""
    
    def initialize_knowledge_base(self):
        """Initialize the vector store with nutrition knowledge"""
        try:
            # Add initial knowledge to vector store
            initial_docs = knowledge_base.initial_knowledge
            if initial_docs:
                vector_store.add_documents(initial_docs)
        except Exception as e:
            print(f"Error initializing knowledge base: {str(e)}")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process nutrition knowledge requests"""
        action = input_data.get("action", "answer")
        
        if action == "answer":
            return await self.answer_question(input_data)
        elif action == "search":
            return await self.search_knowledge(input_data)
        elif action == "add_knowledge":
            return await self.add_knowledge(input_data)
        elif action == "get_categories":
            return await self.get_categories()
        else:
            return {"error": f"Unknown action: {action}"}
    
    async def answer_question(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Answer a nutrition question using RAG"""
        try:
            question = input_data.get("question", "")
            context = input_data.get("context", "")
            user_profile = input_data.get("user_profile", {})
            
            if not question:
                return {"error": "Question is required"}
            
            # Search for relevant knowledge
            relevant_docs = vector_store.similarity_search_with_score(question, k=3)
            
            # Prepare context from retrieved documents
            retrieved_context = ""
            sources = []
            if relevant_docs:
                for doc, score in relevant_docs:
                    if score < 0.8:  # Only use relevant documents
                        retrieved_context += f"\n{doc.page_content}\n"
                        sources.append(doc.metadata.get("source", "Knowledge Base"))
            
            # Build personalized prompt
            prompt = self._build_question_prompt(
                question=question,
                retrieved_context=retrieved_context,
                context=context,
                user_profile=user_profile
            )
            
            # Generate response
            response = await self.generate_response(prompt)
            
            # Extract related questions if possible
            related_questions = await self._get_related_questions(question)
            
            return {
                "success": True,
                "question": question,
                "answer": response,
                "sources": list(set(sources)) if sources else ["General Nutrition Knowledge"],
                "related_questions": related_questions,
                "retrieved_docs_count": len(relevant_docs)
            }
            
        except Exception as e:
            return {"error": f"Error answering question: {str(e)}"}
    
    async def search_knowledge(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Search the knowledge base for relevant information"""
        try:
            query = input_data.get("query", "")
            category = input_data.get("category", "")
            k = input_data.get("k", 5)
            
            if not query:
                return {"error": "Search query is required"}
            
            # Search vector store
            if category:
                # Filter by category if specified
                category_docs = knowledge_base.get_knowledge_by_category(category)
                if category_docs:
                    # Create temporary vector store with category docs
                    from rag.vector_store import VectorStore
                    temp_store = VectorStore()
                    temp_store.vector_store.add_documents(category_docs)
                    results = temp_store.similarity_search_with_score(query, k=k)
                else:
                    results = []
            else:
                results = vector_store.similarity_search_with_score(query, k=k)
            
            # Format results
            search_results = []
            for doc, score in results:
                search_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "relevance_score": float(score)
                })
            
            return {
                "success": True,
                "query": query,
                "results": search_results,
                "total_results": len(search_results)
            }
            
        except Exception as e:
            return {"error": f"Error searching knowledge: {str(e)}"}
    
    async def add_knowledge(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add new knowledge to the base"""
        try:
            question = input_data.get("question", "")
            answer = input_data.get("answer", "")
            category = input_data.get("category", "general")
            source = input_data.get("source", "User Input")
            
            if not question or not answer:
                return {"error": "Question and answer are required"}
            
            # Create new document
            new_doc = knowledge_base.add_knowledge_item(question, answer, category, source)
            
            # Add to vector store
            success = vector_store.add_documents([new_doc])
            
            if success:
                return {
                    "success": True,
                    "message": "Knowledge added successfully",
                    "document_id": str(id(new_doc)),
                    "category": category
                }
            else:
                return {"error": "Failed to add knowledge to vector store"}
                
        except Exception as e:
            return {"error": f"Error adding knowledge: {str(e)}"}
    
    async def get_categories(self) -> Dict[str, Any]:
        """Get all available knowledge categories"""
        try:
            categories = knowledge_base.get_categories()
            return {
                "success": True,
                "categories": categories,
                "total_categories": len(categories)
            }
        except Exception as e:
            return {"error": f"Error getting categories: {str(e)}"}
    
    def _build_question_prompt(
        self, 
        question: str, 
        retrieved_context: str, 
        context: str, 
        user_profile: Dict[str, Any]
    ) -> str:
        """Build a comprehensive prompt for answering nutrition questions"""
        
        prompt_parts = []
        
        # Add user profile context if available
        if user_profile:
            profile_info = []
            if user_profile.get("goal"):
                profile_info.append(f"Goal: {user_profile['goal']}")
            if user_profile.get("age"):
                profile_info.append(f"Age: {user_profile['age']}")
            if user_profile.get("dietary_restrictions"):
                profile_info.append(f"Dietary restrictions: {user_profile['dietary_restrictions']}")
            if user_profile.get("allergies"):
                profile_info.append(f"Allergies: {user_profile['allergies']}")
            
            if profile_info:
                prompt_parts.append(f"USER PROFILE:\n{', '.join(profile_info)}")
        
        # Add additional context
        if context:
            prompt_parts.append(f"ADDITIONAL CONTEXT:\n{context}")
        
        # Add retrieved knowledge
        if retrieved_context:
            prompt_parts.append(f"RELEVANT KNOWLEDGE:\n{retrieved_context}")
        
        # Add the main question
        prompt_parts.append(f"QUESTION:\n{question}")
        
        # Add instructions
        prompt_parts.append("""
        Please provide a comprehensive answer to the question using the knowledge provided above.
        If the knowledge doesn't fully address the question, supplement with general nutrition expertise.
        Consider the user's profile when providing recommendations.
        Structure your answer to be:
        1. Clear and direct
        2. Evidence-based
        3. Practical and actionable
        4. Personalized when possible
        
        If the question requires medical advice, always recommend consulting with a healthcare provider.
        """)
        
        return "\n\n".join(prompt_parts)
    
    async def _get_related_questions(self, question: str) -> List[str]:
        """Generate related questions based on the current question"""
        try:
            prompt = f"""
            Based on this nutrition question: "{question}"
            
            Generate 3-5 related questions that the user might find helpful.
            The questions should be relevant and expand on the original topic.
            Return only the questions, one per line.
            """
            
            response = await self.generate_response(prompt)
            related_questions = [q.strip() for q in response.split('\n') if q.strip()]
            return related_questions[:5]  # Limit to 5 questions
            
        except Exception as e:
            print(f"Error generating related questions: {str(e)}")
            return []
