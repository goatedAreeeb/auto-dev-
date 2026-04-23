"""Production entrypoint for Hugging Face Spaces and local dev."""

import os
import uvicorn  # type: ignore[import-untyped]

from app.main import app  # noqa: F401

import threading
import uvicorn
from app.ui import demo

def run_backend():
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)

# Start backend in background
threading.Thread(target=run_backend, daemon=True).start()

# Start Gradio UI
demo.launch(server_name="0.0.0.0", server_port=7860)
