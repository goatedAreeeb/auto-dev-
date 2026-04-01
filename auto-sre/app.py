"""Production entrypoint for Hugging Face Spaces and local dev.

Reads PORT from the environment (HF Spaces injects its own PORT value).
Falls back to 7860 to match HF Spaces default expectations.
"""

import os
import uvicorn  # type: ignore[import-untyped]

from app.main import app  # noqa: F401 — ensures all routes are registered

port = int(os.environ.get("PORT", 7860))

# Unconditionally run uvicorn to ensure HF Spaces does not bypass the startup
uvicorn.run(
    app,
    host="0.0.0.0",
    port=port,
)
