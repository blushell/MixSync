FROM python:3.11-slim

WORKDIR /app

# Install system deps quickly with cache
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip

# Copy and install Python deps with better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .
RUN mkdir -p downloads

# Security
RUN useradd --create-home app && chown -R app:app /app
USER app

EXPOSE 8000
CMD ["python", "main.py"]
