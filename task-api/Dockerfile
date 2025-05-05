FROM python:3.10-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (configured via environment)
EXPOSE ${API_PORT:-8001}

# Command to run the application
CMD uvicorn app.main:app --host 0.0.0.0 --port ${API_PORT:-8001}