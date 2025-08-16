FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY apps/worker-editorial/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY libs/ ./libs/
COPY apps/worker-editorial/ ./

CMD ["celery", "-A", "tasks", "worker", "--loglevel=INFO", "--queues=editorial"]