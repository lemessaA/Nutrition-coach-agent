from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from config import settings
from database.connection import init_db
from api.routers import chat, profile, meal_plan, analyze_food, foods, marketplace


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    await init_db()
    yield
    # Release provider HTTP sessions on shutdown.
    try:
        from providers import get_registry
        await get_registry().close()
    except Exception:
        pass


app = FastAPI(
    title="Nutrition Coach AI Agent",
    description="An AI-powered nutrition coaching system with personalized meal planning and nutrition advice",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS (see CORS_ORIGINS / settings.cors_origins)
_cors_origins = [
    o.strip() for o in settings.cors_origins.split(",") if o.strip()
]
if not _cors_origins:
    _cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(profile.router, prefix="/api/v1", tags=["profile"])
app.include_router(meal_plan.router, prefix="/api/v1", tags=["meal-plan"])
app.include_router(analyze_food.router, prefix="/api/v1", tags=["analyze-food"])
app.include_router(foods.router, prefix="/api/v1", tags=["foods"])
app.include_router(marketplace.router, prefix="/api/v1", tags=["marketplace"])

# Serve locally-uploaded listing images. The directory is created on first
# upload by the marketplace router; we make sure it exists here so the static
# mount never fails at startup even on a fresh checkout.
UPLOADS_DIR = Path(__file__).resolve().parent / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


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