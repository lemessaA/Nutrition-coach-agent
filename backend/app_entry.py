"""
FastAPI / ASGI entrypoint for the API package under ``backend/``.

The backend uses imports such as ``from config import settings`` (paths
relative to the ``backend/`` directory). This module prepends that directory
to ``sys.path`` and re-exports the ``app`` instance, so the root project can
use ``app_entry:app`` with ``fastapi dev`` and ``fastapi deploy`` (e.g. FastAPI
Cloud) from the repository root.
"""

import sys
from pathlib import Path

_backend = Path(__file__).resolve().parent / "backend"
_backend_str = str(_backend)
if _backend_str not in sys.path:
    sys.path.insert(0, _backend_str)

from main import app  # noqa: E402

__all__ = ["app"]
