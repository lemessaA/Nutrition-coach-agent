"""
FastAPI / ASGI entrypoint alongside ``main.py`` in ``backend/``.

The backend uses imports such as ``from config import settings`` (paths
relative to the ``backend/`` directory). This module prepends that directory
to ``sys.path`` and re-exports the ``app`` instance, so you can use
``app_entry:app`` with ``uvicorn`` and ``fastapi dev`` when the current working
directory is ``backend/`` (see ``[tool.fastapi]`` in ``backend/pyproject.toml``).
"""

import sys
from pathlib import Path

_backend = Path(__file__).resolve().parent
_backend_str = str(_backend)
if _backend_str not in sys.path:
    sys.path.insert(0, _backend_str)

from main import app  # noqa: E402

__all__ = ["app"]
