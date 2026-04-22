# Nutrition Coach Agent

A full-stack application that combines a **FastAPI** backend, a **Next.js** (App Router) frontend, and **LangGraph**-driven agents to help users with profiles, chat-based coaching, food analysis, meal planning, and an optional **food marketplace** (buyer and seller roles).

Interactive API documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) when the backend is running.

---

## Table of contents

- [Features](#features)
- [Architecture](#architecture)
- [Technology stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Local development](#local-development)
- [API overview](#api-overview)
- [Project layout](#project-layout)
- [Testing](#testing)
- [Security notes](#security-notes)
- [Contributing](#contributing)
- [License](#license)

---

## Features

| Area | Description |
|------|-------------|
| **Coaching chat** | Natural-language Q&A routed through a LangGraph workflow to specialized agents (coaching, meal planning, food analysis, nutrition knowledge). |
| **User profiles** | User accounts, health profile fields, and optional `buyer` / `seller` / `both` roles for the marketplace. |
| **Meal plans** | Generate and store meal plans; includes a data-backed synthesizer as a reliable fallback. |
| **Food analysis** | Parse meals and food descriptions for estimated nutrition; optional history and summaries per user. |
| **External food data** | Search, barcode, and natural-language queries via a pluggable provider layer (e.g. Open Food Facts, USDA, Nutritionix when keys are configured). |
| **Marketplace** | Sellers create listings with nutrition and pricing; buyers search by nutrients and place orders. Listing images can be **uploaded** from the client and served from `/uploads` on the API host. |
| **Frontend** | Responsive UI, sign-in and profile flows, light/dark theme, marketplace browse/sell/orders pages. |

---

## Architecture

- **Client** (Next.js) calls REST endpoints under `/api/v1/`.
- **Server** (FastAPI) authenticates and validates input with Pydantic, persists to SQLAlchemy models, and serves static uploads for marketplace images.
- **Orchestration** uses LangGraph: user messages are classified and dispatched to the appropriate agent node.
- **LLM** access is centralized (e.g. OpenAI or Groq) via a shared service; optional RAG/vector storage supports nutrition knowledge where configured.

```text
Browser  →  Next.js (localhost:3000)
                ↓ HTTP
         FastAPI (localhost:8000)  →  SQLAlchemy (SQLite or PostgreSQL)
                ↓
         LangGraph + agents  →  LLM / RAG / external food APIs
```

---

## Technology stack

| Layer | Technologies |
|-------|----------------|
| **Backend** | Python 3.11+, FastAPI, Uvicorn, SQLAlchemy, Pydantic Settings, LangChain, LangGraph |
| **Frontend** | Next.js 14, React 18, TypeScript, Tailwind CSS, Radix UI |
| **Data** | SQLite or PostgreSQL (configurable `DATABASE_URL`) |
| **Optional** | FAISS/Chroma, external nutrition APIs (USDA, Nutritionix, etc.) |

Dependencies are listed in `pyproject.toml` and `requirements.txt`; the web client uses `frontend/package.json`.

---

## Prerequisites

- **Python** 3.11 or newer  
- **Node.js** 18 or newer and npm  
- **API keys** for at least one LLM provider (OpenAI and/or Groq), plus any optional food APIs you want to enable  

---

## Configuration

Create a **`.env`** file in the **repository root** (same level as `pyproject.toml`). The backend loads it automatically when the working directory is correct; running commands from the `backend/` directory with a root `.env` is a common pattern—adjust paths or symlink if needed.

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | SQLAlchemy URL (e.g. `sqlite:///./backend/nutrition_coach.db` or a PostgreSQL URL) |
| `GROQ_API_KEY` or `OPENAI_API_KEY` | LLM access (set at least one, matching `LLM_PROVIDER`) |
| `LLM_PROVIDER` | e.g. `groq` or `openai` |
| `LLM_MODEL` | Model id for the chosen provider |
| `USDA_API_KEY` | Optional: USDA FoodData Central |
| `NUTRITIONIX_APP_ID` / `NUTRITIONIX_API_KEY` | Optional: Nutritionix natural nutrients |
| `SECRET_KEY` | Change from default for any deployment that issues tokens |

**Frontend:** copy `frontend/.env.example` to `frontend/.env.local` and set:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Do not commit `.env` or `frontend/.env.local`; they are listed in `.gitignore`.

---

## Local development

### 1. Backend

From the **repository root**:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Optional: pip install -e .   # editable install from pyproject.toml
```

From the **`backend/`** directory (so imports like `config` resolve as in this project):

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

If you use the FastAPI CLI (same `backend` directory):

```bash
cd backend
fastapi dev main.py
```

The app exposes **GET `/health`** for a quick check.

### 2. Frontend

```bash
cd frontend
cp .env.example .env.local   # if you do not already have .env.local
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Ensure `NEXT_PUBLIC_API_URL` points at the same host and port as the API (default `http://127.0.0.1:8000`).

The database is initialized on application startup (FastAPI lifespan).

---

## API overview

All JSON routes are prefixed with **`/api/v1`**. The complete, executable contract is in the OpenAPI UI at `/docs`.

| Tag | Description |
|-----|-------------|
| **Chat** | `POST /chat`, history and sessions |
| **Profile** | User CRUD, health profile, by-email lookup, role updates |
| **Meal plan** | Create/list/get/delete plans, suggestions, weekly generation |
| **Analyze food** | Analyze food, meal, compare, history, summaries |
| **Foods** | `GET /foods/search`, `GET /foods/barcode/{barcode}`, `POST /foods/natural` |
| **Marketplace** | Listings, orders, status updates, `POST /marketplace/uploads` for images |
| **Static** | `GET /uploads/{filename}` for uploaded listing images (mounted on the API app) |

Root routes: `GET /`, `GET /health`.

**Example (chat):**

```bash
curl -s -X POST "http://127.0.0.1:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is a good high-protein breakfast?", "user_id": 1, "session_id": "demo"}'
```

`user_id` and `session_id` are optional. See the `ChatRequest` schema in `/docs`.

---

## Project layout

```text
backend/           # FastAPI app, agents, graph, database, providers
frontend/          # Next.js app (app router, components, services)
data/              # Local datasets and assets used by tools (where applicable)
tests/             # Python tests
docker/            # Container-related files (optional)
pyproject.toml     # Project metadata and Python dependencies
requirements.txt   # Pip-installable list mirroring the backend stack
```

---

## Testing

```bash
# From repository root, with the virtual environment activated
pytest tests/ -q
```

Add or expand tests as you change agents and routes.

---

## Security notes

- **Never** commit real API keys, database passwords, or `frontend/.env.local`.
- Rotate any key that was ever exposed in version control.
- For production, use a strong `SECRET_KEY`, HTTPS, a managed database, and environment-specific CORS (the default CORS list in `main.py` is for local development).

---

## Contributing

1. Open an issue to describe the change or bug.  
2. Fork the repository and create a branch from `main`.  
3. Keep changes focused; follow existing code style.  
4. Run tests and linters before submitting a pull request.  
5. Reference related issues in the PR description.  

---

## License

This project is released under the **MIT License**. See the [`LICENSE`](LICENSE) file in the repository root for the full text.
