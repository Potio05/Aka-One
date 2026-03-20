FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install PyTorch CPU first (heavy layer caching)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium dependencies for the Huawei Modem Reboot spoofing
RUN playwright install chromium --with-deps

# Copy application code
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1

# (Command is overridden in docker-compose)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
