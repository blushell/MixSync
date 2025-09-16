"""Configuration management for MixSync."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration."""
    
    # Spotify API
    SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
    SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
    SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI', 'http://127.0.0.1:8888/callback')
    
    # Playlist settings
    _playlist_id = os.getenv('SPOTIFY_PLAYLIST_ID')
    SPOTIFY_PLAYLIST_ID = f"spotify:playlist:{_playlist_id}" if _playlist_id and not _playlist_id.startswith('spotify:playlist:') else _playlist_id
    POLL_INTERVAL_SECONDS = int(os.getenv('POLL_INTERVAL_SECONDS', 30))
    
    # Download settings
    DOWNLOAD_PATH = Path(os.getenv('DOWNLOAD_PATH', './downloads'))
    MAX_RECENT_DOWNLOADS = int(os.getenv('MAX_RECENT_DOWNLOADS', 10))
    
    # Web server settings
    WEB_HOST = os.getenv('WEB_HOST', 'localhost')
    WEB_PORT = int(os.getenv('WEB_PORT', 3000))
    
    # Logging settings
    ENABLE_FILE_LOGGING = os.getenv('ENABLE_FILE_LOGGING', 'true').lower() in ('true', '1', 'yes', 'on')
    
    # Metadata settings
    ENABLE_METADATA_TAGGING = os.getenv('ENABLE_METADATA_TAGGING', 'true').lower() in ('true', '1', 'yes', 'on')
    ENABLE_BPM_DETECTION = os.getenv('ENABLE_BPM_DETECTION', 'true').lower() in ('true', '1', 'yes', 'on')
    DEFAULT_GENRE = os.getenv('DEFAULT_GENRE', 'Electronic')
    
    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration values."""
        errors = []
        
        if not cls.SPOTIPY_CLIENT_ID:
            errors.append("SPOTIPY_CLIENT_ID is required")
        if not cls.SPOTIPY_CLIENT_SECRET:
            errors.append("SPOTIPY_CLIENT_SECRET is required")
        if not cls.SPOTIFY_PLAYLIST_ID:
            errors.append("SPOTIFY_PLAYLIST_ID is required")
            
        return errors
    
    @classmethod
    def setup_directories(cls):
        """Create necessary directories."""
        cls.DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)
