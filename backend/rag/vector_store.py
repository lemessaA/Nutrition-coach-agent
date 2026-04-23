from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores import Chroma
from config import settings
import os


class VectorStore:
    """FAISS/Chroma storage for the nutrition RAG path.

    No embedding backend is configured in this project (the chat LLM is Groq only).
    The vector store stays inert until an embedding class is wired here (e.g. local
    HuggingFace models); RAG then calls ``initialize_store()``.
    """

    def __init__(self) -> None:
        self.embeddings: Optional[object] = None
        
        self.vector_store = None
        self.initialized = False
    
    def initialize_store(self):
        """Initialize the vector store based on configuration"""
        if not self.embeddings:
            print("Warning: Cannot initialize vector store without embeddings")
            return
            
        store_path = settings.vector_db_path
        
        try:
            if settings.vector_db_type == "faiss":
                if os.path.exists(f"{store_path}.faiss"):
                    self.vector_store = FAISS.load_local(
                        store_path, 
                        self.embeddings,
                        allow_dangerous_deserialization=True
                    )
                else:
                    self.vector_store = FAISS.from_texts(
                        ["Initializing nutrition knowledge base"], 
                        self.embeddings
                    )
                    self.save_store()
            elif settings.vector_db_type == "chroma":
                self.vector_store = Chroma(
                    persist_directory=store_path,
                    embedding_function=self.embeddings
                )
            
            self.initialized = True
        except Exception as e:
            print(f"Warning: Failed to initialize vector store: {e}")
            self.vector_store = None
    
    def save_store(self):
        """Save the vector store to disk"""
        if settings.vector_db_type == "faiss" and self.vector_store:
            self.vector_store.save_local(settings.vector_db_path)
        elif settings.vector_db_type == "chroma":
            self.vector_store.persist()
    
    def add_documents(self, documents: List[Document]) -> bool:
        """Add documents to the vector store"""
        if not self.vector_store:
            return False
        try:
            if settings.vector_db_type == "faiss":
                self.vector_store.add_documents(documents)
            else:
                self.vector_store.add_documents(documents)
            
            self.save_store()
            return True
        except Exception as e:
            print(f"Error adding documents: {str(e)}")
            return False
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Search for similar documents"""
        if not self.vector_store:
            return []
        try:
            return self.vector_store.similarity_search(query, k=k)
        except Exception as e:
            print(f"Error searching documents: {str(e)}")
            return []
    
    def similarity_search_with_score(self, query: str, k: int = 5) -> List[tuple]:
        """Search for similar documents with relevance scores"""
        if not self.vector_store:
            return []
        try:
            return self.vector_store.similarity_search_with_score(query, k=k)
        except Exception as e:
            print(f"Error searching documents with scores: {str(e)}")
            return []


# Global vector store instance
vector_store = VectorStore()