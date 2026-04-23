"""Production entrypoint for Hugging Face Spaces and local dev."""

import os
import uvicorn  # type: ignore[import-untyped]

from app.main import app  # noqa: F401

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
    )
