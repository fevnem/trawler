FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    "fastapi>=0.115" \
    "uvicorn[standard]>=0.30" \
    "yt-dlp>=2026.1.1" \
    "httpx>=0.28" \
    "pydantic-settings>=2.4" \
    "mcp>=2.3"

COPY src ./src

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# One worker on purpose: the concurrency limiters and ticket key live in process.
CMD ["uvicorn", "trawler.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
