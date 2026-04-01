# Environment and DevOps

## 1. Local Development Environment

### 1.1 Prerequisites
| Tool        | Version   | Purpose                        |
| :---------- | :-------- | :----------------------------- |
| Python      | 3.10+     | Runtime                        |
| pip / venv  | Latest    | Dependency management          |
| Docker      | 24+       | Containerization               |
| Git         | 2.40+     | Version control                |

### 1.2 Setup Steps
```bash
# Clone the repository
git clone https://github.com/your-org/auto-sre.git
cd auto-sre

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# Install dependencies
pip install -e ".[dev]"

# Run the development server
uvicorn app.main:app --reload --port 8000
```

---

## 2. Docker Configuration

### 2.1 Dockerfile
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.2 Docker Compose (Dev)
```yaml
version: "3.9"
services:
  auto-sre:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - ENV=development
      - LOG_LEVEL=debug
```

---

## 3. Deployment Target: Hugging Face Spaces

### 3.1 Configuration
| Setting            | Value                      |
| :----------------- | :------------------------- |
| **SDK**            | Docker                     |
| **Hardware**       | CPU Basic (free tier)      |
| **Port**           | 8000                       |
| **Visibility**     | Public                     |

### 3.2 Deployment Steps
1. Push the repository to a Hugging Face Space (type: Docker).
2. Ensure the `Dockerfile` is at the repository root.
3. Hugging Face auto-builds and serves the container.
4. Verify endpoints at `https://<space-name>.hf.space/docs`.

---

## 4. Environment Variables
| Variable       | Default        | Description                              |
| :------------- | :------------- | :--------------------------------------- |
| `ENV`          | `production`   | Environment mode (`development` / `production`) |
| `LOG_LEVEL`    | `info`         | Logging verbosity (`debug`, `info`, `warning`) |
| `STEP_TIMEOUT` | `5`            | Max seconds per step execution           |
| `HOST`         | `0.0.0.0`      | Server bind address                      |
| `PORT`         | `8000`         | Server port                              |

---

## 5. CI/CD Pipeline (GitHub Actions)

### 5.1 Workflow: `.github/workflows/ci.yml`
```yaml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: mypy .
      - run: pytest --cov=app --cov=engine --cov=grader -v

  docker:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t auto-sre .
      - run: docker run --rm auto-sre python -m pytest
```

---

## 6. Monitoring & Logging
* **Structured Logging:** Use Python `logging` with JSON output for production.
* **Health Endpoint:** `GET /state` doubles as a liveness probe.
* **Metrics (Post-MVP):** Prometheus counters for `steps_total`, `episodes_total`, `avg_reward`.
