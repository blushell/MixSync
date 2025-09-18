# Docker Setup for MixSync

This document provides instructions for running MixSync using Docker. The application is containerized with a `Dockerfile` and can be orchestrated using `docker-compose.yml` for easier management of volumes and environment variables.

## Prerequisites

- Docker installed on your system (version 20.10 or later)
- Docker Compose installed (version 1.29 or later; included in Docker Desktop)
- GitHub account (for GHCR integration, optional)
- A `.env` file in the project root with your Spotify credentials and other configuration (copy from `env_example.txt`)

## Building and Running with Docker Compose (Recommended)

Docker Compose handles building the image, mounting volumes for data persistence, and managing environment variables.

### 1. Prepare Environment

Copy the example environment file and fill in your credentials:

```bash
cp env_example.txt .env
# Edit .env with your SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIFY_PLAYLIST_ID, etc.
```

Ensure the `downloads` directory exists (it will be created automatically):

```bash
mkdir -p downloads
```

### 2. Build and Start

Build the image and start the containers:

```bash
docker-compose up --build -d
```

- The `-d` flag runs in detached mode (background).
- The application will be available at `http://localhost:3000`.
- Logs can be viewed with `docker-compose logs -f`.

### 3. Stop and Remove

To stop the containers:

```bash
docker-compose down
```

To stop and remove volumes (warning: this deletes downloads and database):

```bash
docker-compose down -v
```

### 4. Volumes and Persistence

- **Downloads**: Mounted at `./downloads` (host) to `/app/downloads` (container). Your downloaded files will persist on the host.
- **Database**: The SQLite database (`audio_fetcher.db`) is mounted to the host root for persistence.
- If you don't want persistence, remove the `volumes` section from `docker-compose.yml`.

### 5. Environment Variables

All configuration is passed via the `.env` file. Key variables:

- `SPOTIPY_CLIENT_ID`: Your Spotify app client ID
- `SPOTIPY_CLIENT_SECRET`: Your Spotify app client secret
- `SPOTIFY_PLAYLIST_ID`: The Spotify playlist ID to monitor
- `DOWNLOAD_PATH`: Path for downloads (defaults to `/app/downloads` in container)
- `WEB_PORT`: Port for the web interface (defaults to 3000)

Update `WEB_HOST=0.0.0.0` in `.env` if accessing from outside localhost.

## Running with Docker (Without Compose)

If you prefer manual Docker commands:

### Build the Image

```bash
docker build -t mixsync .
```

### Run the Container

```bash
docker run -d \
  --name mixsync \
  -p 3000:3000 \
  -v $(pwd)/downloads:/app/downloads \
  -v $(pwd)/audio_fetcher.db:/app/audio_fetcher.db \
  --env-file .env \
  --restart unless-stopped \
  mixsync
```

### View Logs

```bash
docker logs -f mixsync
```

### Stop and Remove

```bash
docker stop mixsync
docker rm mixsync
```

## GitHub Container Registry (GHCR) Integration

To build and push the Docker image to GitHub Container Registry for deployment (e.g., to a server or GitHub Actions).

### 1. Enable GHCR in Your Repository

- Go to your GitHub repository settings.
- Under "Packages", ensure GHCR is enabled (it's automatic for public repos).

### 2. Build and Push Manually

Authenticate with GitHub:

```bash
# Login to GHCR (replace with your GitHub username)
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

Build and tag the image:

```bash
docker build -t ghcr.io/YOUR_GITHUB_USERNAME/mixsync:latest .
```

Push the image:

```bash
docker push ghcr.io/YOUR_GITHUB_USERNAME/mixsync:latest
```

Replace `YOUR_GITHUB_USERNAME` with your GitHub username and `mixsync` with your repo name if different.

### 3. Using GitHub Actions (Automated)

Create `.github/workflows/docker-build.yml` for automatic builds on push:

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata for Docker
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

- Commit and push this workflow file.
- The image will be built and pushed to `ghcr.io/YOUR_USERNAME/REPO_NAME:latest` on pushes to main.

### 4. Pull and Run from GHCR

```bash
docker pull ghcr.io/YOUR_GITHUB_USERNAME/mixsync:latest
docker run -d -p 3000:3000 --env-file .env -v ./downloads:/app/downloads ghcr.io/YOUR_GITHUB_USERNAME/mixsync:latest
```

## Troubleshooting

- **Permission Issues**: Ensure the `downloads` directory has write permissions (`chmod 755 downloads`).
- **Database Locked**: If SQLite locks occur, restart the container or check for concurrent access.
- **Port Conflict**: Change `WEB_PORT` in `.env` if 3000 is in use.
- **Missing ffmpeg**: The Dockerfile installs ffmpeg for audio processing (yt-dlp dependency).
- **Logs**: Use `docker-compose logs mixsync` or `docker logs mixsync` for debugging.
- **Health Check Failing**: Ensure the app starts properly; check logs for errors like missing env vars.
- **Spotify Auth**: The redirect URI in Spotify app settings should match your setup (default: http://127.0.0.1:8888/callback). For Docker, it works with localhost.

## Development

For development with hot-reloading:

- Mount the source code: Add `-v $(pwd):/app` to `docker run` or volumes in compose (but exclude `.git`, `node_modules`, etc., via `.dockerignore`).
- Use `docker-compose up --build` for rebuilds.

Create a `.dockerignore` file:

```
.git
__pycache__
*.pyc
.env
audio_fetcher.db
downloads/
.DS_Store
```

For more details, see the [Docker documentation](https://docs.docker.com/) and [GitHub Container Registry docs](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).
