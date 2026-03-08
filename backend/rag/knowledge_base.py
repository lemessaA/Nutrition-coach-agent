from typing import List, Dict, Any
from langchain_core.documents import Document
import json
import os


class NutritionKnowledgeBase:
    """Manages the nutrition knowledge base with initial data and updates"""
    
    def __init__(self):
        self.initial_knowledge = self._load_initial_knowledge()
    
    def _load_initial_knowledge(self) -> List[Document]:
        """Load initial nutrition knowledge"""
        knowledge_items = [
            {
                "category": "protein",
                "question": "How much protein should I eat daily?",
                "answer": "The recommended daily protein intake is 0.8g per kg of body weight for sedentary adults, 1.2-1.6g for active individuals, and 1.6-2.2g for athletes or those trying to build muscle. Protein is essential for muscle repair, immune function, and hormone production.",
                "source": "Nutrition Guidelines"
            },
            {
                "category": "protein",
                "question": "What are the best sources of protein?",
                "answer": "Excellent protein sources include lean meats (chicken, turkey), fish (salmon, tuna), eggs, dairy products (Greek yogurt, cottage cheese), legumes (beans, lentils), tofu, tempeh, and protein supplements. Choose a variety of sources to get all essential amino acids.",
                "source": "Nutrition Science"
            },
            {
                "category": "carbs",
                "question": "Are carbohydrates bad for weight loss?",
                "answer": "Carbohydrates are not inherently bad for weight loss. They are the body's primary energy source. Choose complex carbs like whole grains, vegetables, and fruits over simple carbs. The key is portion control and timing, especially around workouts.",
                "source": "Sports Nutrition"
            },
            {
                "category": "carbs",
                "question": "What's the difference between simple and complex carbs?",
                "answer": "Simple carbs (sugar, white bread, candy) digest quickly and can cause blood sugar spikes. Complex carbs (oats, brown rice, vegetables) digest slowly, providing sustained energy and fiber. Complex carbs are generally better for overall health and weight management.",
                "source": "Nutrition Basics"
            },
            {
                "category": "fats",
                "question": "Are all fats unhealthy?",
                "answer": "No, fats are essential for health. Healthy fats include monounsaturated (avocado, olive oil, nuts) and polyunsaturated (omega-3 fatty acids in fish, flaxseeds). Limit saturated fats and avoid trans fats. Fats help with vitamin absorption and hormone production.",
                "source": "Lipid Research"
            },
            {
                "category": "vitamins",
                "question": "What vitamins are most important for energy?",
                "answer": "B vitamins (B1, B2, B3, B5, B6, B12) are crucial for energy metabolism. They help convert food into energy. Iron, vitamin C, and magnesium also play important roles in energy production and reducing fatigue.",
                "source": "Micronutrient Research"
            },
            {
                "category": "hydration",
                "question": "How much water should I drink daily?",
                "answer": "General guidelines suggest 8-10 cups (64-80oz) daily, but needs vary by activity level, climate, and body size. Athletes may need more. A good rule is to drink enough that your urine is pale yellow. Monitor thirst and urine color as indicators.",
                "source": "Hydration Guidelines"
            },
            {
                "category": "weight_loss",
                "question": "What's a healthy rate of weight loss?",
                "answer": "A healthy weight loss rate is 1-2 pounds (0.5-1kg) per week. This ensures you're losing fat rather than muscle and is more sustainable long-term. Very rapid weight loss often leads to muscle loss and weight regain.",
                "source": "Weight Management Research"
            },
            {
                "category": "meal_timing",
                "question": "When should I eat around workouts?",
                "answer": "Eat a balanced meal 2-3 hours before exercise. For early morning workouts, have a light snack 30-60 minutes before. Within 30-60 minutes post-workout, consume protein and carbs to optimize recovery and muscle synthesis.",
                "source": "Sports Nutrition"
            },
            {
                "category": "supplements",
                "question": "What supplements are actually beneficial?",
                "answer": "Evidence-based supplements include: Vitamin D (especially in winter), Omega-3 fish oil (for heart and brain health), Creatine (for strength/power), Protein powder (for convenience), and Magnesium (if deficient). Always prioritize whole foods first.",
                "source": "Supplement Research"
            },
            {
                "category": "fiber",
                "question": "How much fiber do I need daily?",
                "answer": "Adults need 25-35g of fiber daily. Fiber aids digestion, helps control blood sugar, and supports heart health. Good sources include vegetables, fruits, whole grains, legumes, nuts, and seeds. Increase fiber intake gradually and drink plenty of water.",
                "source": "Fiber Research"
            },
            {
                "category": "nutrition_labels",
                "question": "How do I read nutrition labels effectively?",
                "answer": "Focus on: serving size (most important), calories per serving, protein, fiber, and limit saturated fat, added sugars, and sodium. Check the ingredient list - fewer ingredients usually means less processed. Look for whole foods as first ingredients.",
                "source": "Nutrition Education"
            }
        ]
        
        documents = []
        for item in knowledge_items:
            content = f"Question: {item['question']}\nAnswer: {item['answer']}"
            metadata = {
                "category": item["category"],
                "question": item["question"],
                "source": item["source"]
            }
            documents.append(Document(page_content=content, metadata=metadata))
        
        return documents
    
    def get_knowledge_by_category(self, category: str) -> List[Document]:
        """Get knowledge items by category"""
        return [doc for doc in self.initial_knowledge if doc.metadata.get("category") == category]
    
    def add_knowledge_item(self, question: str, answer: str, category: str, source: str = "User Input") -> Document:
        """Add a new knowledge item"""
        content = f"Question: {question}\nAnswer: {answer}"
        metadata = {
            "category": category,
            "question": question,
            "source": source
        }
        return Document(page_content=content, metadata=metadata)
    
    def get_categories(self) -> List[str]:
        """Get all available categories"""
        categories = set()
        for doc in self.initial_knowledge:
            if "category" in doc.metadata:
                categories.add(doc.metadata["category"])
        return list(categories)


# Global knowledge base instance
knowledge_base = NutritionKnowledgeBase()
