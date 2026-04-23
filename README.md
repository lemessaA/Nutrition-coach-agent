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
- [Deploy frontend (Vercel)](#deploy-frontend-vercel)
- [FastAPI Cloud deployment](#fastapi-cloud-deployment)
- [Docker deployment](#docker-deployment)
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

Create a **`.env`** file in the **repository root** (same level as `pyproject.toml`). The backend loads it via an explicit path (`backend/config.py`), so it works whether you start Uvicorn from `backend/`, the repo root, or Docker. Copy from [`.env.example`](.env.example) and fill in secrets—**never commit** `.env` (it is gitignored).

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Optional. SQLAlchemy URL for **PostgreSQL** or another server DB. If unset, the app defaults to a **SQLite** file under `backend/nutrition_coach.db` (path resolved from `config.py`, not the shell cwd). |
| `GROQ_API_KEY` or `OPENAI_API_KEY` | LLM access (set at least one, matching `LLM_PROVIDER`) |
| `LLM_PROVIDER` | e.g. `groq` or `openai` |
| `LLM_MODEL` | Model id for the chosen provider |
| `USDA_API_KEY` | Optional: USDA FoodData Central |
| `NUTRITIONIX_APP_ID` / `NUTRITIONIX_API_KEY` | Optional: Nutritionix natural nutrients |
| `SECRET_KEY` | Change from default for any deployment that issues tokens |
| `CORS_ORIGINS` | Comma-separated browser origins allowed to call the API (default: `http://localhost:3000,http://127.0.0.1:3000`). Add your LAN or production URL (e.g. `https://your-app.example.com`) when you deploy. |

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

### Run from the repository root (same entry as FastAPI Cloud)

The ASGI app is also exposed as **`app_entry:app`**, with `sys.path` adjusted so the code in `backend/` keeps working. This matches the `[tool.fastapi]` entrypoint in `pyproject.toml`:

```bash
# From the repository root (not only from backend/)
fastapi dev
# or: uvicorn app_entry:app --reload --host 0.0.0.0 --port 8000
```

If `fastapi` is not found, install the CLI with: `pip install "fastapi[standard]"`.

---

## Deploy frontend (Vercel)

The **Next.js app** in [`frontend/`](frontend/) is intended to run on [Vercel](https://vercel.com) (or any Node host). The **FastAPI** backend must be deployed separately and reachable over **HTTPS** in production.

1. **Deploy the API** (Docker, a VPS, FastAPI Cloud, etc.) and note its public origin with **no trailing slash**, e.g. `https://api.yourdomain.com`.
2. **CORS** on the API: set `CORS_ORIGINS` in the backend environment to your Vercel URL(s), for example:
   - `https://your-app.vercel.app`
   - Your custom domain: `https://app.yourdomain.com`
   - For **preview deployments**, add each preview URL you use, or a pattern your platform supports—FastAPI accepts a **comma-separated list** of exact origins.
3. In the [Vercel dashboard](https://vercel.com/dashboard): **Add New… → Project** → import this Git repository.
4. **Root Directory**: set to **`frontend`** (required for this monorepo). Vercel will detect Next.js using [`frontend/vercel.json`](frontend/vercel.json).
5. **Environment variables** (Production, and optionally Preview):
   - `NEXT_PUBLIC_API_URL` = your API origin, e.g. `https://api.yourdomain.com` (same value the browser will use; **no** trailing slash).
6. **Deploy**, then open the generated `.vercel.app` URL. Redeploy after changing `NEXT_PUBLIC_API_URL` so the client bundle picks it up.

**CLI (optional):** from the repo, `cd frontend && npx vercel` and link the project; set the same env vars when prompted or in the dashboard.

[`frontend/lib/public-api-url.ts`](frontend/lib/public-api-url.ts) centralizes the API base URL. [`frontend/next.config.js`](frontend/next.config.js) allows `next/image` to load listing assets from `NEXT_PUBLIC_API_URL` under `/uploads/`.

---

## FastAPI Cloud deployment

[FastAPI Cloud](https://fastapicloud.com/) runs your FastAPI app with `fastapi deploy` and the [FastAPI Cloud CLI](https://fastapicloud.com/docs/fastapi-cloud-cli/deploy/) (bundled with `fastapi[standard]`). This repository is set up to deploy **from the repository root** so you do not need a separate `main.py` at the top level: see [`app_entry.py`](app_entry.py) and `[tool.fastapi]` in [`pyproject.toml`](pyproject.toml).

1. **Install** the CLI (in a venv is recommended):
   ```bash
   pip install "fastapi[standard]"
   ```
2. **Log in** (browser flow on first use):
   ```bash
   fastapi login
   ```
3. **Set environment variables** in the cloud (Postgres and secrets are recommended for anything beyond a quick test). Examples:
   ```bash
   fastapi cloud env set DATABASE_URL "postgresql://user:pass@host:5432/dbname"
   fastapi cloud env set --secret GROQ_API_KEY "your-key"
   fastapi cloud env set CORS_ORIGINS "https://your-frontend.example.com,https://your-app.vercel.app"
   fastapi cloud env set SECRET_KEY "a-long-random-string"
   ```
   Use [`fastapi cloud env set`](https://fastapicloud.com/docs/fastapi-cloud-cli/) for the full set of subcommands, or set variables in the [dashboard](https://dashboard.fastapicloud.com/) under your app.
4. **Deploy** from the **repository root**:
   ```bash
   fastapi deploy
   ```
   A `.fastapicloud` directory is created to link this project to your cloud app. Subsequent updates are a single `fastapi deploy`.

**Notes:**

- The default `DATABASE_URL` in `config.py` is for local development. **Use a managed PostgreSQL URL** in cloud; SQLite is usually unsuitable for serverless or multi-instance hosting.
- Set **`CORS_ORIGINS`** to your real front-end origin(s) (for example a Vercel URL); the app uses `allow_credentials=True`, so you cannot rely on a wildcard.
- If your account is on a **wait list**, use the [FastAPI Cloud](https://fastapicloud.com/) site to request access, then repeat the steps above.
- [Official docs: existing project](https://fastapicloud.com/docs/getting-started/existing-project/) and [configuring the entrypoint](https://fastapicloud.com/docs/builds-and-deployments/configuring-fastapi/).

---

## Docker deployment

If you want a **reproducible, self-hosted** stack instead of a managed host (e.g. FastAPI Cloud), use Docker. This repo includes:

| File | Purpose |
|------|---------|
| [`Dockerfile`](Dockerfile) | Builds the API from `app_entry:app` and `backend/` (Python 3.12). |
| [`docker-compose.yml`](docker-compose.yml) | Runs **PostgreSQL 16** and the **API** on the same user-defined network, with a volume for marketplace **uploads**. |
| [`env.docker.example`](env.docker.example) | Copy to `.env` in the project root; put API keys and CORS there (do not commit). |
| [`.dockerignore`](.dockerignore) | Keeps the image small (excludes `frontend/`, `node_modules/`, venv, etc.). |

**Why Docker vs FastAPI Cloud**

| | Docker (Compose) | FastAPI Cloud |
|---|------------------|----------------|
| **You operate** | Servers, images, optional reverse proxy, DB backups | The platform (scaling, HTTPS, build pipeline) |
| **Database** | You add Postgres in Compose or use an external DSN | Set `DATABASE_URL` in the cloud dashboard or CLI |
| **Typical use** | VPS, on-prem, air-gapped, full control | Fastest “run `fastapi deploy`” path |

**Quick start**

1. `cp env.docker.example .env` and set at least `GROQ_API_KEY` (or `OPENAI_API_KEY`) and `CORS_ORIGINS` (include your real front-end origin in production).  
2. `docker compose up --build`  
3. API: [http://localhost:8000](http://localhost:8000) — docs at `/docs`.  

Compose reads **`POSTGRES_USER`**, **`POSTGRES_PASSWORD`**, and **`POSTGRES_DB`** from `.env` (see [`env.docker.example`](env.docker.example)). The same values are used to build the API `DATABASE_URL` pointing at the internal `db` service—**no database passwords belong in `docker-compose.yml` or in source code.** PostgreSQL data lives in the `postgres_data` volume; uploaded listing images in `marketplace_uploads`.  

**API image only (no Compose)**

```bash
docker build -t nutrition-coach-api .
docker run --rm -p 8000:8000 --env-file .env nutrition-coach-api
```

Set `DATABASE_URL` to a reachable database (e.g. managed Postgres) when not using the Compose `db` service.

**RAG / `data/`**

If you store vector or CSV data under `data/`, add a volume in `docker-compose.yml` (e.g. `./data:/app/data`) or extend the `Dockerfile` to `COPY data/` when that directory exists in your branch.

**Front end**

The Next.js app is not in this image. Run it on the host with `cd frontend && npm run dev`, deploy it to Vercel, or add a second `Dockerfile` under `frontend/` if you need a containerized UI.

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
app_entry.py      # ASGI entry for ``fastapi dev`` / FastAPI Cloud / Docker (imports backend app)
Dockerfile         # API container image
docker-compose.yml # API + PostgreSQL (optional local stack)
env.docker.example # Template for variables used with Compose / ``docker run``
backend/          # FastAPI app, agents, graph, database, providers
frontend/         # Next.js app (Vercel: use this folder as root; includes vercel.json)
data/             # Local datasets and assets used by tools (where applicable)
tests/            # Python tests
pyproject.toml    # Project metadata, dependencies, and [tool.fastapi] entrypoint
requirements.txt  # Pip-installable list mirroring the backend stack
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
- For production, use a strong `SECRET_KEY`, HTTPS, a managed database, and set `CORS_ORIGINS` to your deployed front-end (defaults are for local development only).

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
