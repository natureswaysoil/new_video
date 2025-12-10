FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY video_automation.py .
COPY scheduler.py .

# Create directories
RUN mkdir -p /app/videos /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the scheduler by default
CMD ["python", "scheduler.py"]
