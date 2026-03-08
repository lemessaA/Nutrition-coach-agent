# Nutrition Coach AI Agent

A comprehensive AI-powered nutrition coaching system built with FastAPI, LangChain, and Next.js. This system provides personalized meal planning, nutrition advice, and habit coaching through multiple specialized AI agents.

## Features

### 🤖 AI-Powered Coaching
- **User Profile Agent**: Collects and manages health information with automatic BMR/TDEE calculations
- **Meal Planner Agent**: Generates personalized daily and weekly meal plans with recipes
- **Nutrition Knowledge Agent**: RAG-powered Q&A system with evidence-based nutrition information
- **Food Analyzer Agent**: Analyzes meals and tracks nutritional intake
- **Coaching Agent**: Provides motivation, habit guidance, and behavioral support
- **Market Intelligence Agent**: Offers budget-friendly nutrition options and market insights

### 🎯 Core Capabilities
- Personalized nutrition recommendations based on health goals
- Automated meal planning with shopping lists
- Food analysis with calorie and macro breakdowns
- Nutrition Q&A with scientific backing
- Habit coaching and motivation
- Budget-conscious meal suggestions

## Architecture

### Backend (FastAPI + Python)
- **FastAPI**: RESTful API framework
- **LangChain + LangGraph**: Multi-agent orchestration and workflow management
- **SQLAlchemy**: Database ORM with SQLite/PostgreSQL support
- **Vector Database**: FAISS/Chroma for nutrition knowledge retrieval
- **Multiple LLM Support**: OpenAI, Groq, and other compatible models

### Frontend (Next.js + TypeScript)
- **Next.js 14**: Modern React framework with App Router
- **Tailwind CSS**: Utility-first styling with shadcn/ui components
- **Responsive Design**: Mobile-first interface
- **Real-time Chat**: Interactive AI coaching interface

### Agent Workflow
```
User Question → Intent Router → Relevant Agent → Response
```

The system uses LangGraph to coordinate between specialized agents based on user intent.

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- OpenAI or Groq API key

### Backend Setup

1. **Clone and navigate to project:**
```bash
git clone <repository-url>
cd Nutrition-coach-agent
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

Required environment variables:
```env
OPENAI_API_KEY=your_openai_key
# or
GROQ_API_KEY=your_groq_key

DATABASE_URL=sqlite:///./nutrition_coach.db
LLM_PROVIDER=openai  # openai or groq
LLM_MODEL=gpt-3.5-turbo
```

5. **Initialize database:**
```bash
python -c "from backend.database.connection import init_db; init_db()"
```

6. **Start the backend server:**
```bash
cd backend
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Set environment variables:**
```bash
cp .env.example .env.local
# Edit .env.local
```

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. **Start the development server:**
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## API Endpoints

### Chat & Coaching
- `POST /api/v1/chat` - Chat with AI nutrition coach
- `GET /api/v1/chat/history/{user_id}` - Get chat history
- `GET /api/v1/chat/sessions/{user_id}` - Get chat sessions

### Profile Management
- `POST /api/v1/profile` - Create user account
- `POST /api/v1/profile/{user_id}/health` - Create health profile
- `PUT /api/v1/profile/{user_id}/health` - Update health profile
- `GET /api/v1/profile/{user_id}/health` - Get health profile
- `GET /api/v1/profile/{user_id}/summary` - Get profile summary

### Meal Planning
- `POST /api/v1/meal-plan` - Generate meal plan
- `GET /api/v1/meal-plan/{user_id}` - Get meal plans
- `POST /api/v1/meal-plan/{user_id}/generate-weekly` - Generate weekly plan
- `GET /api/v1/meal-plan/{user_id}/suggestions` - Get meal suggestions

### Food Analysis
- `POST /api/v1/analyze-food` - Analyze food nutrition
- `POST /api/v1/analyze-meal` - Analyze complete meal
- `POST /api/v1/compare-foods` - Compare multiple foods
- `GET /api/v1/analyze-food/{user_id}/history` - Get analysis history

## Usage Examples

### Chat with the AI Coach
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a meal plan for weight loss",
    "session_id": "user123"
  }'
```

### Create User Profile
```bash
curl -X POST "http://localhost:8000/api/v1/profile/1/health" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 30,
    "weight": 70,
    "height": 175,
    "gender": "male",
    "activity_level": "moderately_active",
    "goal": "lose_weight"
  }'
```

### Analyze Food
```bash
curl -X POST "http://localhost:8000/api/v1/analyze-food" \
  -H "Content-Type: application/json" \
  -d '{
    "food_input": "chicken breast with rice and vegetables",
    "user_id": 1
  }'
```

## Agent Capabilities

### User Profile Agent
- Calculates BMR using Mifflin-St Jeor equation
- Determines TDEE based on activity level
- Sets personalized macro targets
- Validates health information

### Meal Planner Agent
- Generates daily/weekly meal plans
- Creates shopping lists
- Considers dietary restrictions and preferences
- Provides recipes with nutritional information

### Nutrition Knowledge Agent
- RAG-powered Q&A system
- Evidence-based nutrition information
- Personalized answers based on user profile
- Source citations and confidence scores

### Food Analyzer Agent
- Parses complex meal descriptions
- Calculates calories and macronutrients
- Provides nutritional insights
- Rates meal quality

### Coaching Agent
- Motivational support and encouragement
- Habit-building strategies
- Progress celebration
- Obstacle overcoming guidance

### Market Intelligence Agent
- Budget-friendly food options
- Seasonal produce recommendations
- Price comparisons
- Market trend analysis

## Development

### Adding New Agents
1. Create agent class in `backend/agents/`
2. Inherit from `BaseAgent`
3. Implement `process()` and `get_system_prompt()` methods
4. Add to agent mapping in `IntentRouter`
5. Update workflow if needed

### Extending Frontend
- Components in `frontend/components/`
- Pages in `frontend/app/`
- API services in `frontend/services/`
- Types in `frontend/types/`

### Database Schema
- Models in `backend/database/models.py`
- Schemas in `backend/schemas/`
- Migration with Alembic

## Configuration

### LLM Settings
```python
# backend/config.py
LLM_PROVIDER = "openai"  # or "groq"
LLM_MODEL = "gpt-3.5-turbo"
```

### Database
```python
DATABASE_URL = "sqlite:///./nutrition_coach.db"
# or PostgreSQL: "postgresql://user:pass@localhost/dbname"
```

### Vector Database
```python
VECTOR_DB_TYPE = "faiss"  # or "chroma"
VECTOR_DB_PATH = "./data/vector_db"
```

## Testing

### Backend Tests
```bash
cd backend
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Integration Testing
```bash
# Start both backend and frontend
npm run test:e2e
```

## Deployment

### Backend (Docker)
```bash
docker build -t nutrition-coach-backend .
docker run -p 8000:8000 nutrition-coach-backend
```

### Frontend (Vercel/Netlify)
Deploy the `frontend` directory to your preferred platform.

### Production Considerations
- Use PostgreSQL for production database
- Set up proper API rate limiting
- Configure HTTPS
- Monitor LLM usage and costs
- Set up logging and monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the API endpoints

## Roadmap

- [ ] Mobile app development
- [ ] Integration with fitness trackers
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Recipe image generation
- [ ] Social features and community