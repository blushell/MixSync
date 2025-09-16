# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for audio processing and yt-dlp
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash mixsync && \
    chown -R mixsync:mixsync /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=mixsync:mixsync . .

# Create directories for downloads and logs
RUN mkdir -p /app/downloads /app/logs && \
    chown -R mixsync:mixsync /app/downloads /app/logs

# Switch to non-root user
USER mixsync

# Expose the web server port
EXPOSE 3000

# Set environment variables
ENV PYTHONPATH=/app
ENV DOWNLOAD_PATH=/app/downloads
ENV WEB_HOST=0.0.0.0
ENV WEB_PORT=3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Default command
CMD ["python", "main.py"]
