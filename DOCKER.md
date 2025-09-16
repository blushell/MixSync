# 🐳 Docker Guide for MixSync

This guide covers everything you need to know about running MixSync with Docker.

## 🚀 Quick Start

### Option 1: GitHub Container Registry (Recommended)

Pull and run the pre-built image:

```bash
# Create necessary directories
mkdir -p downloads logs data

# Create your .env file
cp env_example.txt .env
# Edit .env with your Spotify credentials

# Run the container
docker run -d \
  --name mixsync \
  -p 3000:3000 \
  -v ./downloads:/app/downloads \
  -v ./logs:/app/logs \
  -v ./data:/app/data \
  --env-file .env \
  --restart unless-stopped \
  ghcr.io/YOUR_USERNAME/mixsync:latest
```

### Option 2: Docker Compose (Best for Development)

```bash
# Clone and setup
git clone <repository-url>
cd mixsync

# Configure environment
cp env_example.txt .env
# Edit .env with your credentials

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f mixsync

# Stop the application
docker-compose down
```

### Option 3: Build Locally

```bash
# Clone the repository
git clone <repository-url>
cd mixsync

# Build the image
docker build -t mixsync .

# Run the container
docker run -d \
  --name mixsync \
  -p 3000:3000 \
  -v ./downloads:/app/downloads \
  -v ./logs:/app/logs \
  -v ./data:/app/data \
  --env-file .env \
  mixsync
```

## 📁 Volume Mounts

MixSync uses three main directories that should be mounted as volumes:

| Container Path   | Purpose                | Required |
| ---------------- | ---------------------- | -------- |
| `/app/downloads` | Downloaded audio files | Yes      |
| `/app/logs`      | Application logs       | Optional |
| `/app/data`      | SQLite database        | Yes      |

### Creating Volumes

```bash
# Create local directories
mkdir -p downloads logs data

# Or use Docker named volumes
docker volume create mixsync-downloads
docker volume create mixsync-logs
docker volume create mixsync-data
```

## 🔧 Configuration

### Environment Variables

All configuration is done through environment variables. Create a `.env` file:

```env
# Required - Spotify API
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_PLAYLIST_ID=your_playlist_id

# Optional - Application Settings
POLL_INTERVAL_SECONDS=30
DOWNLOAD_PATH=/app/downloads
WEB_HOST=0.0.0.0
WEB_PORT=3000
ENABLE_FILE_LOGGING=true
ENABLE_METADATA_TAGGING=true
ENABLE_BPM_DETECTION=true
DEFAULT_GENRE=Electronic
```

### Docker-Specific Variables

These are automatically set in the container:

- `PYTHONPATH=/app`
- `DOWNLOAD_PATH=/app/downloads`
- `WEB_HOST=0.0.0.0` (allows external connections)
- `WEB_PORT=3000`

## 🔗 Network Configuration

### Port Mapping

The container exposes port 3000. Map it to your desired host port:

```bash
# Standard mapping
-p 3000:3000

# Custom host port
-p 8080:3000

# Only localhost access
-p 127.0.0.1:3000:3000
```

### Docker Compose Network

```yaml
version: '3.8'
services:
  mixsync:
    # ... other config
    ports:
      - '3000:3000' # host:container
    networks:
      - mixsync-network

networks:
  mixsync-network:
    driver: bridge
```

## 🏥 Health Checks

The container includes a built-in health check:

```bash
# Check container health
docker ps

# View health check logs
docker inspect mixsync --format='{{.State.Health.Status}}'

# Manual health check
curl http://localhost:3000/health
```

Health check endpoint returns:

```json
{
	"status": "healthy",
	"download_path": "/app/downloads",
	"download_path_exists": true
}
```

## 📊 Monitoring & Logs

### Viewing Logs

```bash
# Real-time logs
docker logs -f mixsync

# With Docker Compose
docker-compose logs -f mixsync

# Last 100 lines
docker logs --tail=100 mixsync

# Logs since specific time
docker logs --since="2024-01-01T00:00:00" mixsync
```

### Log Levels

Control logging with environment variables:

```env
# Enable file logging (logs to /app/logs/)
ENABLE_FILE_LOGGING=true

# Python logging level (DEBUG, INFO, WARNING, ERROR)
PYTHONLOGLEVEL=INFO
```

### Container Stats

```bash
# Resource usage
docker stats mixsync

# Container details
docker inspect mixsync

# Process list
docker exec mixsync ps aux
```

## 🛠️ Development with Docker

### Development Mode

Use the development compose file for live code reloading:

```bash
# Start in development mode
docker-compose -f docker-compose.dev.yml up -d

# Mount source code for live reload
# Changes to Python files will restart the server
```

### Debugging

```bash
# Execute shell in running container
docker exec -it mixsync bash

# View container environment
docker exec mixsync env

# Check Python packages
docker exec mixsync pip list

# Test connectivity
docker exec mixsync curl http://localhost:3000/health
```

### Building Development Images

```bash
# Build with development target
docker build --target development -t mixsync:dev .

# Build with specific Python version
docker build --build-arg PYTHON_VERSION=3.11 -t mixsync .
```

## 🔄 Updates & Maintenance

### Updating the Container

#### Using GitHub Container Registry

```bash
# Pull latest image
docker pull ghcr.io/YOUR_USERNAME/mixsync:latest

# Stop current container
docker stop mixsync
docker rm mixsync

# Run with new image
docker run -d \
  --name mixsync \
  -p 3000:3000 \
  -v ./downloads:/app/downloads \
  -v ./logs:/app/logs \
  -v ./data:/app/data \
  --env-file .env \
  ghcr.io/YOUR_USERNAME/mixsync:latest
```

#### Using Docker Compose

```bash
# Pull and restart with new image
docker-compose pull
docker-compose up -d
```

### Backup & Recovery

#### Backup Data

```bash
# Backup downloads and database
tar -czf mixsync-backup-$(date +%Y%m%d).tar.gz downloads/ data/

# Backup specific database
cp data/audio_fetcher.db backups/audio_fetcher_$(date +%Y%m%d).db
```

#### Restore Data

```bash
# Extract backup
tar -xzf mixsync-backup-20240101.tar.gz

# Start container with restored data
docker-compose up -d
```

## 🚨 Troubleshooting

### Common Issues

#### Container Won't Start

```bash
# Check logs for errors
docker logs mixsync

# Check if port is in use
netstat -tulpn | grep :3000

# Try different port
docker run -p 8080:3000 ...
```

#### Permission Issues

```bash
# Fix volume permissions
sudo chown -R 1000:1000 downloads/ logs/ data/

# Or use root user (not recommended)
docker run --user root ...
```

#### Out of Disk Space

```bash
# Check container size
docker system df

# Clean up unused containers/images
docker system prune -a

# Remove old containers
docker container prune
```

#### Network Issues

```bash
# Check if container can reach internet
docker exec mixsync ping google.com

# Check internal networking
docker exec mixsync curl http://localhost:3000/health

# Restart networking
docker network prune
```

### Performance Tuning

#### Resource Limits

```yaml
# docker-compose.yml
services:
  mixsync:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
```

#### Environment Optimization

```env
# Reduce BPM detection for better performance
ENABLE_BPM_DETECTION=false

# Increase polling interval to reduce CPU usage
POLL_INTERVAL_SECONDS=60

# Disable file logging for better I/O
ENABLE_FILE_LOGGING=false
```

## 🔒 Security

### Best Practices

1. **Use specific image tags** instead of `:latest`
2. **Mount volumes read-only** when possible
3. **Use secrets** for sensitive environment variables
4. **Run as non-root user** (automatically done in our image)
5. **Keep images updated** regularly

### Secrets Management

#### Docker Secrets

```bash
# Create secret
echo "your_spotify_client_secret" | docker secret create spotify_secret -

# Use in compose
version: '3.8'
services:
  mixsync:
    secrets:
      - spotify_secret
    environment:
      - SPOTIPY_CLIENT_SECRET_FILE=/run/secrets/spotify_secret

secrets:
  spotify_secret:
    external: true
```

#### Environment Files

```bash
# Use separate env file for secrets
docker run --env-file secrets.env ...

# Or mount as volume
docker run -v ./secrets.env:/app/.env ...
```

## 📋 Reference

### Complete Docker Run Command

```bash
docker run -d \
  --name mixsync \
  --restart unless-stopped \
  -p 3000:3000 \
  -v ./downloads:/app/downloads \
  -v ./logs:/app/logs \
  -v ./data:/app/data \
  --env-file .env \
  --health-cmd="curl -f http://localhost:3000/health || exit 1" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  --memory=1g \
  --cpus=0.5 \
  ghcr.io/YOUR_USERNAME/mixsync:latest
```

### Available Image Tags

- `ghcr.io/YOUR_USERNAME/mixsync:latest` - Latest stable release
- `ghcr.io/YOUR_USERNAME/mixsync:main` - Latest main branch
- `ghcr.io/YOUR_USERNAME/mixsync:develop` - Development branch
- `ghcr.io/YOUR_USERNAME/mixsync:v1.0.0` - Specific version tags

### Useful Commands

```bash
# Container management
docker start mixsync
docker stop mixsync
docker restart mixsync
docker rm mixsync

# Image management
docker images
docker rmi mixsync
docker pull ghcr.io/YOUR_USERNAME/mixsync:latest

# Cleanup
docker system prune -a
docker volume prune
docker network prune
```

---

For more information, check the main [README.md](README.md) or open an issue on GitHub.
