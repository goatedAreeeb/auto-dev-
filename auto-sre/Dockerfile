FROM python:3.10-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .

# HF Spaces requires port 7860; PORT env var overrides this
EXPOSE 7860

CMD ["python", "app.py"]
