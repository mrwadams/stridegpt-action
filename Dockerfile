# STRIDE-GPT GitHub Action Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy action code
COPY src/ ./src/
COPY entrypoint.py .

# Create non-root user
RUN useradd -m -u 1000 stride && chown -R stride:stride /app
USER stride

# Run the action
ENTRYPOINT ["python", "entrypoint.py"]