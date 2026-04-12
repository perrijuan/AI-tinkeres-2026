"""Compatibility entrypoint.

Keeps support for `uvicorn src.main:app` while using the integrated app
implemented in backend/main.py.
"""

from main import app  # re-export
