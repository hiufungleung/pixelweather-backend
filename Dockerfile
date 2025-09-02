FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data logs && chown -R appuser:appuser /app

# Expose port (will be configurable via env var)
EXPOSE 5001

# Set environment variables for production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_ENV=production
ENV DEBUG=False

# Switch to non-root user
USER appuser

# Health check using dedicated script (works without exposing ports)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python healthcheck.py

# Use Gunicorn for production
CMD ["gunicorn", "--config", "gunicorn.conf.py", "main:app"]