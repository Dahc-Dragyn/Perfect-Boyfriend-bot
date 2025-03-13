FROM python:3.10-slim

WORKDIR /app

# Install necessary packages and clean up
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py persona.py ./
COPY static ./static
COPY templates ./templates

# Expose the port.  8080 is the Cloud Run default.
EXPOSE 8080

# Use environment variables, but set defaults.
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV GEMINI_API_KEY=${GEMINI_API_KEY}
ENV MODEL_NAME=gemini-1.5-flash
ENV MAX_WORKERS=5
ENV CACHE_MAXSIZE=1024
ENV CACHE_TTL=300
ENV PORT=8080

CMD uvicorn main:app --host 0.0.0.0 --port $PORT