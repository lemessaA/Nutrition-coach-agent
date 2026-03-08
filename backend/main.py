from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from database.connection import init_db
from api.routers import chat, profile, meal_plan, analyze_food


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    await init_db()
    yield


app = FastAPI(
    title="Nutrition Coach AI Agent",
    description="An AI-powered nutrition coaching system with personalized meal planning and nutrition advice",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(profile.router, prefix="/api/v1", tags=["profile"])
app.include_router(meal_plan.router, prefix="/api/v1", tags=["meal-plan"])
app.include_router(analyze_food.router, prefix="/api/v1", tags=["analyze-food"])


@app.get("/")
async def root():
    return {"message": "Nutrition Coach AI Agent API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug
    )