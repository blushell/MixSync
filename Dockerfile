# Use a lightweight Python image
FROM python:3.11-slim

# Install system dependencies (ffmpeg + build tools)
RUN apt-get update && apt-get install -y --no-install-recommends     ffmpeg     build-essential     && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (to leverage Docker cache)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Create downloads folder if not already present
RUN mkdir -p /app/downloads

# Expose FastAPI port
EXPOSE 8000

# Set environment variables (optional)
ENV PYTHONUNBUFFERED=1

# Run FastAPI app with uvicorn
CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
