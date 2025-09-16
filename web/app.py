"""FastAPI web application for manual audio downloads."""

import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import uvicorn
from typing import Dict, List

from services.download_service import DownloadService
from services.database_service import DatabaseService
from config import Config

logger = logging.getLogger(__name__)

app = FastAPI(title="MixSync", description="Audio Download Service")

# Setup templates and static files
templates = Jinja2Templates(directory="web/templates")
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Initialize services
download_service = DownloadService()
database_service = DatabaseService()

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/history", response_class=HTMLResponse)
async def history(request: Request):
    """Serve the download history page."""
    return templates.TemplateResponse("history.html", {"request": request})

@app.post("/download")
async def start_download(url: str = Form(...), filename: str = Form(None)):
    """Start a download job."""
    try:
        # Validate URL
        if not url or not url.strip():
            return JSONResponse(
                status_code=400, 
                content={"error": "URL is required"}
            )
        
        url = url.strip()
        custom_filename = filename.strip() if filename and filename.strip() else None
        
        # Create a unique download ID
        download_id = f"download_{len(manager.active_connections)}_{hash(url)}"
        
        # Start download asynchronously
        asyncio.create_task(
            process_download(download_id, url, custom_filename)
        )
        
        return JSONResponse(content={
            "status": "started",
            "download_id": download_id,
            "url": url,
            "filename": custom_filename
        })
        
    except Exception as e:
        logger.error(f"Error starting download: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

async def process_download(download_id: str, url: str, custom_filename: str = None):
    """Process download and send updates via WebSocket."""
    
    def progress_callback(progress_info):
        """Send progress updates to all connected clients."""
        message = {
            "type": "progress",
            "download_id": download_id,
            "data": progress_info
        }
        asyncio.create_task(manager.broadcast(json.dumps(message)))
    
    try:
        # Send start message
        start_message = {
            "type": "start",
            "download_id": download_id,
            "url": url,
            "filename": custom_filename
        }
        await manager.broadcast(json.dumps(start_message))
        
        # Add download record to database
        db_id = await database_service.add_download(
            filename=custom_filename or f"download_{download_id}",
            original_url=url,
            source_type='manual'
        )
        
        # Perform download
        result = await download_service.download_audio(
            url, 
            custom_filename, 
            progress_callback
        )
        
        # Update database record with completion status
        if result['status'] == 'completed' and result.get('filepath'):
            file_path = Path(result['filepath'])
            file_size = file_path.stat().st_size if file_path.exists() else 0
            
            # Extract metadata for database
            metadata = download_service.metadata_service.extract_metadata_from_filename(file_path.name)
            
            await database_service.update_download_success(
                download_id=db_id,
                file_path=str(file_path),
                file_size=file_size
            )
            
            # Update with artist and track info if available
            if metadata.get('artist') or metadata.get('title'):
                await database_service.update_download_metadata(
                    download_id=db_id,
                    artist=metadata.get('artist'),
                    track_name=metadata.get('title')
                )
                
        elif result['status'] == 'error':
            await database_service.update_download_failed(
                download_id=db_id,
                error_message=result.get('error', 'Unknown error')
            )
        
        # Send completion message
        complete_message = {
            "type": "complete",
            "download_id": download_id,
            "data": result
        }
        await manager.broadcast(json.dumps(complete_message))
        
        logger.info(f"Download {download_id} completed: {result.get('status')}")
        
    except Exception as e:
        logger.error(f"Download {download_id} failed: {e}")
        error_message = {
            "type": "error",
            "download_id": download_id,
            "error": str(e)
        }
        await manager.broadcast(json.dumps(error_message))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            logger.debug(f"Received WebSocket message: {data}")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/supported-sites")
async def get_supported_sites():
    """Get list of supported download sites."""
    try:
        sites = download_service.get_supported_sites()
        # Return a subset of popular sites for the UI
        popular_sites = [
            'youtube', 'soundcloud', 'bandcamp', 'vimeo', 
            'dailymotion', 'mixcloud', 'audiomack'
        ]
        
        # If we got sites, filter for popular ones, otherwise use the fallback
        if sites:
            supported_popular = [site for site in popular_sites if site in sites]
            if not supported_popular:
                # If no matches found, return the first few from the full list
                supported_popular = sites[:7] if len(sites) >= 7 else sites
        else:
            # Fallback to popular sites list
            supported_popular = popular_sites
        
        return JSONResponse(content={
            "popular_sites": supported_popular,
            "total_supported": len(sites) if sites else len(popular_sites)
        })
        
    except Exception as e:
        logger.error(f"Error getting supported sites: {e}")
        # Return fallback data instead of error
        return JSONResponse(content={
            "popular_sites": ['youtube', 'soundcloud', 'bandcamp', 'vimeo', 'dailymotion', 'mixcloud'],
            "total_supported": 1000
        })

@app.get("/api/downloads")
async def get_downloads():
    """Get list of downloaded files."""
    try:
        download_path = Config.DOWNLOAD_PATH
        if not download_path.exists():
            return JSONResponse(content={"files": []})
        
        files = []
        for file_path in download_path.glob("*.mp3"):
            stat = file_path.stat()
            files.append({
                "name": file_path.name,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "path": str(file_path.relative_to(download_path))
            })
        
        # Sort by creation time (newest first)
        files.sort(key=lambda x: x['created'], reverse=True)
        
        # Limit to configured number of recent downloads
        limited_files = files[:Config.MAX_RECENT_DOWNLOADS]
        
        return JSONResponse(content={
            "files": limited_files,
            "total_files": len(files),
            "showing": len(limited_files),
            "limit": Config.MAX_RECENT_DOWNLOADS
        })
        
    except Exception as e:
        logger.error(f"Error getting downloads: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to get downloads"}
        )

@app.get("/api/download-stats")
async def get_download_stats():
    """Get download statistics from database."""
    try:
        stats = await database_service.get_download_stats()
        return JSONResponse(content=stats)
        
    except Exception as e:
        logger.error(f"Error getting download stats: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to get download statistics"}
        )

@app.get("/api/download-history")
async def get_download_history(
    page: int = 1,
    limit: int = 50,
    search: str = None,
    status: str = None,
    source: str = None
):
    """Get paginated download history from database."""
    try:
        offset = (page - 1) * limit
        
        # Get downloads with filters
        downloads = await database_service.get_all_downloads(
            limit=limit,
            offset=offset,
            status_filter=status,
            source_filter=source
        )
        
        # If search term provided, use search instead
        if search and search.strip():
            downloads = await database_service.search_downloads(
                search_term=search.strip(),
                limit=limit
            )
        
        # Get total count for pagination
        total_count = await database_service.get_count(
            status_filter=status,
            source_filter=source
        )
        
        total_pages = (total_count + limit - 1) // limit
        
        return JSONResponse(content={
            "downloads": downloads,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total": total_count,
                "limit": limit,
                "offset": offset
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting download history: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to get download history"}
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(content={
        "status": "healthy",
        "download_path": str(Config.DOWNLOAD_PATH),
        "download_path_exists": Config.DOWNLOAD_PATH.exists()
    })

if __name__ == "__main__":
    # Setup logging
    def setup_logging():
        """Setup logging configuration based on config settings."""
        handlers = [logging.StreamHandler()]
        
        # Add file handler only if enabled in config
        if Config.ENABLE_FILE_LOGGING:
            handlers.append(logging.FileHandler('audio_fetcher.log'))
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=handlers
        )
    
    setup_logging()
    
    # Ensure download directory exists
    Config.setup_directories()
    
    # Run the server
    uvicorn.run(
        "web.app:app",
        host=Config.WEB_HOST,
        port=Config.WEB_PORT,
        reload=True,
        log_level="info"
    )
