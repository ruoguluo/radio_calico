# Multi-stage Dockerfile for Radio Russell
# Supports both development and production builds

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Development stage
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir flask-debugtoolbar ipython

# Copy all source code
COPY . .

# Create data directory for database
RUN mkdir -p /app/data

# Set environment for development
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1
ENV DATABASE_PATH=/app/data/database.db

# Expose port
EXPOSE 3000

# Run development server
CMD ["python", "app.py"]

# Production stage
FROM base as production

# Install production WSGI server
RUN pip install --no-cache-dir gunicorn

# Create non-root user for security
RUN groupadd -r radiouser && useradd -r -g radiouser radiouser

# Copy source code
COPY --chown=radiouser:radiouser . .

# Create data directory with proper permissions and setup service worker
RUN mkdir -p /app/data && chown -R radiouser:radiouser /app/data && \
    cp static/sw.js sw.js 2>/dev/null || true && \
    chown radiouser:radiouser sw.js 2>/dev/null || true

# Set environment for production
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0
ENV DATABASE_PATH=/app/data/database.db

# Switch to non-root user
USER radiouser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run production server with gunicorn using optimized app
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "app_optimized:app"]
