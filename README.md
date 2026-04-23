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
- [Backend on Render](#backend-on-render)
- [Deploy frontend (Vercel)](#deploy-frontend-vercel)
- [FastAPI Cloud deployment](#fastapi-cloud-deployment)
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
| **Backend** | Python 3.11+, [uv](https://docs.astral.sh/uv/) (`uv pip` for packages), FastAPI, Uvicorn, SQLAlchemy, Pydantic Settings, LangChain, LangGraph |
| **Frontend** | Next.js 14, React 18, TypeScript, Tailwind CSS, Radix UI |
| **Data** | SQLite or PostgreSQL (configurable `DATABASE_URL`) |
| **Optional** | FAISS/Chroma, external nutrition APIs (USDA, Nutritionix, etc.) |

Backend Python dependencies are listed in `backend/pyproject.toml` and the repo-root `requirements.txt` — install them with **`uv pip`** (see [Local development](#local-development)). The web client uses `frontend/package.json`.

---

## Prerequisites

- **Python** 3.11 or newer  
- **[uv](https://docs.astral.sh/uv/)** for Python packages (`uv pip`). Install: see [Getting started](https://docs.astral.sh/uv/getting-started/installation/) (e.g. `curl -LsSf https://astral.sh/uv/install.sh | sh` on Linux/macOS).  
- **Node.js** 18 or newer and npm  
- **API keys** for at least one LLM provider (OpenAI and/or Groq), plus any optional food APIs you want to enable  

---

## Configuration

Create a **`.env`** file in the **repository root** (same level as `requirements.txt`). The backend loads it via an explicit path (`backend/config.py`), so it works whether you start Uvicorn from `backend/` or the repo root. Copy from [`.env.example`](.env.example) and fill in secrets—**never commit** `.env` (it is gitignored).

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

Use **[uv](https://docs.astral.sh/uv/)** and **`uv pip`** (not plain `pip`) for dependencies. From the **repository root**:

```bash
uv venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
# Optional: uv pip install -e backend/   # editable install using backend/pyproject.toml
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

The ASGI app is also exposed as **`app_entry:app`**, with `sys.path` adjusted so the code in `backend/` keeps working. This matches the `[tool.fastapi]` entrypoint in `backend/pyproject.toml`:

```bash
# From the repository root (not only from backend/)
fastapi dev
# or: uvicorn app_entry:app --reload --host 0.0.0.0 --port 8000
```

If `fastapi` is not found, install the CLI with: `uv pip install "fastapi[standard]"` (with your venv activated).

---

## Backend on Render

The API runs on [Render](https://render.com) as a **Web Service** with the **Python** runtime. The repo includes [`render.yaml`](render.yaml) ([Blueprint spec](https://render.com/docs/blueprint-spec)). The build runs **`uv pip install --system -r requirements.txt`** (after installing `uv` with `pip`) so the same lockfile as local dev is used; the start command is `uvicorn app_entry:app` on `$PORT`.

- **URL:** `https://<service-name>.onrender.com` (or a custom domain). **No trailing slash.**
- **Health check:** path **`/health`**.
- **Database:** Add [Render PostgreSQL](https://render.com/docs/databases) and set **`DATABASE_URL`** to the **Internal** connection string (web service and DB in the same region). Do not use the default SQLite path in production; Render filesystems for free web services are not durable for a DB file.
- **Free tier:** The web service may spin down when idle; the first request can be slow.

### Deploy the API and connect [Vercel](https://vercel.com) (this project)

**Frontend in production:** [https://nutrition-coach-agent-kappa.vercel.app/](https://nutrition-coach-agent-kappa.vercel.app/)

1. **Push** this repository to GitHub (if it is not already).
2. In [Render Dashboard](https://dashboard.render.com) → **New +** → **Blueprint** (or **Web Service** if you prefer manual setup) → connect the repo. Render will read [`render.yaml`](render.yaml).
3. When prompted, set:
   - **`GROQ_API_KEY`** — your [Groq](https://console.groq.com) API key (required for chat/agents).
   - **`DATABASE_URL`** — after you create a **PostgreSQL** instance (Render: **New +** → **PostgreSQL**), paste the **Internal Database URL** into the web service environment (same region as the service).
4. **`CORS_ORIGINS`** in [`render.yaml`](render.yaml) already includes `https://nutrition-coach-agent-kappa.vercel.app` plus local `http://localhost:3000` / `http://127.0.0.1:3000`. Add more origins (e.g. Vercel preview URLs) in the **Environment** tab as a comma-separated list, **no spaces** after commas.
5. **Deploy** the web service. Copy its URL, e.g. `https://nutrition-coach-api.onrender.com` (your name may differ).
6. In [Vercel](https://vercel.com) → your project **nutrition-coach-agent** (or the linked repo) → **Settings** → **Environment Variables** → set  
   `NEXT_PUBLIC_API_URL` = `https://<your-render-service>.onrender.com`  
   (no trailing slash). Apply to **Production** (and **Preview** if you want previews to call the same API). **Redeploy** the frontend so the new URL is embedded in the client bundle.
7. Test: open the Vercel site, sign in, chat — requests should go to the Render host. Check browser devtools **Network** if something fails (often CORS or a wrong `NEXT_PUBLIC_API_URL`).

**Secrets in Render (Environment):**

| Key | Notes |
|-----|--------|
| `GROQ_API_KEY` | Set in the dashboard when deploying. |
| `DATABASE_URL` | Render Postgres internal URL, or any accessible `postgresql://…` |
| `CORS_ORIGINS` | Browsers’ origins (Vercel), not the API URL. |
| `SECRET_KEY` | Blueprint can generate one; you may override in the dashboard. |

---

## Deploy frontend (Vercel)

The **Next.js app** in [`frontend/`](frontend/) is intended to run on [Vercel](https://vercel.com) (or any Node host). The **FastAPI** backend is usually on **Render** (above) or another host, reachable over **HTTPS**.

1. **Note the API origin** (e.g. `https://<name>.onrender.com`) with **no trailing slash**.
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
   uv pip install "fastapi[standard]"
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
app_entry.py      # ASGI entry for ``fastapi dev`` / FastAPI Cloud / Render (imports backend app)
render.yaml        # Optional Render Blueprint (Python) for the API
backend/          # FastAPI app, agents, graph, database, providers; ``backend/pyproject.toml`` metadata
frontend/         # Next.js app (Vercel: use this folder as root; includes vercel.json)
data/             # Local datasets and assets used by tools (where applicable)
tests/            # Python tests
requirements.txt  # Python deps (install: ``uv pip install -r requirements.txt``)
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
