"""Database service for tracking download history using SQLite."""

import aiosqlite
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from config import Config

logger = logging.getLogger(__name__)

class DatabaseService:
    """Manages SQLite database operations for download tracking."""
    
    def __init__(self):
        """Initialize database service."""
        self.db_path = Path("audio_fetcher.db")  # Store in project root
        # Ensure downloads directory exists for other purposes
        Config.DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)
        
    async def initialize(self):
        """Initialize the database and create tables if they don't exist."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS downloads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        original_url TEXT,
                        source_type TEXT,  -- 'playlist' or 'manual'
                        file_size INTEGER,
                        file_path TEXT,
                        artist TEXT,
                        track_name TEXT,
                        search_query TEXT,
                        spotify_track_id TEXT,
                        download_status TEXT,  -- 'completed', 'failed', 'processing'
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP
                    )
                """)
                
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_downloads_created_at 
                    ON downloads(created_at DESC)
                """)
                
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_downloads_status 
                    ON downloads(download_status)
                """)
                
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_downloads_source 
                    ON downloads(source_type)
                """)
                
                await db.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    async def add_download(self, 
                          filename: str,
                          original_url: str = None,
                          source_type: str = 'manual',
                          artist: str = None,
                          track_name: str = None,
                          search_query: str = None,
                          spotify_track_id: str = None) -> int:
        """Add a new download record and return the ID.
        
        Args:
            filename: Name of the downloaded file
            original_url: Original URL that was downloaded
            source_type: 'playlist' or 'manual'
            artist: Artist name (for playlist downloads)
            track_name: Track name (for playlist downloads)
            search_query: Search query used (for playlist downloads)
            spotify_track_id: Spotify track ID (for playlist downloads)
        
        Returns:
            Database ID of the created record
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    INSERT INTO downloads 
                    (filename, original_url, source_type, artist, track_name, 
                     search_query, spotify_track_id, download_status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'processing', ?)
                """, (filename, original_url, source_type, artist, track_name,
                      search_query, spotify_track_id, datetime.now().isoformat()))
                
                download_id = cursor.lastrowid
                await db.commit()
                
                logger.info(f"Added download record: {filename} (ID: {download_id})")
                return download_id
                
        except Exception as e:
            logger.error(f"Error adding download record: {e}")
            raise
    
    async def update_download_success(self, 
                                    download_id: int,
                                    file_path: str,
                                    file_size: int):
        """Update download record when download completes successfully.
        
        Args:
            download_id: Database ID of the download record
            file_path: Path to the downloaded file
            file_size: Size of the downloaded file in bytes
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE downloads 
                    SET download_status = 'completed',
                        file_path = ?,
                        file_size = ?,
                        completed_at = ?
                    WHERE id = ?
                """, (file_path, file_size, datetime.now().isoformat(), download_id))
                
                await db.commit()
                logger.info(f"Updated download record {download_id} as completed")
                
        except Exception as e:
            logger.error(f"Error updating download success: {e}")
    
    async def update_download_failed(self, 
                                   download_id: int,
                                   error_message: str):
        """Update download record when download fails.
        
        Args:
            download_id: Database ID of the download record
            error_message: Error message describing the failure
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE downloads 
                    SET download_status = 'failed',
                        error_message = ?,
                        completed_at = ?
                    WHERE id = ?
                """, (error_message, datetime.now().isoformat(), download_id))
                
                await db.commit()
                logger.info(f"Updated download record {download_id} as failed")
                
        except Exception as e:
            logger.error(f"Error updating download failure: {e}")
    
    async def update_download_metadata(self, 
                                     download_id: int,
                                     artist: str = None,
                                     track_name: str = None):
        """Update artist and track name for a download record.
        
        Args:
            download_id: Database ID of the download record
            artist: Artist name to set
            track_name: Track name to set
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE downloads 
                    SET artist = ?, track_name = ?
                    WHERE id = ?
                """, (artist, track_name, download_id))
                
                await db.commit()
                logger.debug(f"Updated metadata for download {download_id}: {artist} - {track_name}")
                
        except Exception as e:
            logger.error(f"Error updating download metadata: {e}")
            raise
    
    async def get_all_downloads(self, 
                               limit: int = None,
                               offset: int = 0,
                               status_filter: str = None,
                               source_filter: str = None) -> List[Dict]:
        """Get all downloads from the database.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            status_filter: Filter by download status ('completed', 'failed', 'processing')
            source_filter: Filter by source type ('playlist', 'manual')
        
        Returns:
            List of download records as dictionaries
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                # Build query with filters
                query = "SELECT * FROM downloads WHERE 1=1"
                params = []
                
                if status_filter:
                    query += " AND download_status = ?"
                    params.append(status_filter)
                
                if source_filter:
                    query += " AND source_type = ?"
                    params.append(source_filter)
                
                query += " ORDER BY created_at DESC"
                
                if limit:
                    query += " LIMIT ? OFFSET ?"
                    params.extend([limit, offset])
                
                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
                    
                    downloads = []
                    for row in rows:
                        download = dict(row)
                        # Convert timestamps to more readable format
                        if download['created_at']:
                            download['created_at_formatted'] = self._format_timestamp(download['created_at'])
                        if download['completed_at']:
                            download['completed_at_formatted'] = self._format_timestamp(download['completed_at'])
                        downloads.append(download)
                    
                    return downloads
                    
        except Exception as e:
            logger.error(f"Error getting downloads: {e}")
            return []
    
    async def get_download_stats(self) -> Dict:
        """Get download statistics.
        
        Returns:
            Dictionary with download statistics
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Total downloads
                async with db.execute("SELECT COUNT(*) FROM downloads") as cursor:
                    total = (await cursor.fetchone())[0]
                
                # Completed downloads
                async with db.execute("SELECT COUNT(*) FROM downloads WHERE download_status = 'completed'") as cursor:
                    completed = (await cursor.fetchone())[0]
                
                # Failed downloads
                async with db.execute("SELECT COUNT(*) FROM downloads WHERE download_status = 'failed'") as cursor:
                    failed = (await cursor.fetchone())[0]
                
                # Processing downloads
                async with db.execute("SELECT COUNT(*) FROM downloads WHERE download_status = 'processing'") as cursor:
                    processing = (await cursor.fetchone())[0]
                
                # Playlist vs manual downloads
                async with db.execute("SELECT COUNT(*) FROM downloads WHERE source_type = 'playlist'") as cursor:
                    playlist_downloads = (await cursor.fetchone())[0]
                
                async with db.execute("SELECT COUNT(*) FROM downloads WHERE source_type = 'manual'") as cursor:
                    manual_downloads = (await cursor.fetchone())[0]
                
                # Total file size
                async with db.execute("SELECT SUM(file_size) FROM downloads WHERE download_status = 'completed'") as cursor:
                    total_size = (await cursor.fetchone())[0] or 0
                
                return {
                    'total_downloads': total,
                    'completed_downloads': completed,
                    'failed_downloads': failed,
                    'processing_downloads': processing,
                    'playlist_downloads': playlist_downloads,
                    'manual_downloads': manual_downloads,
                    'total_file_size': total_size,
                    'success_rate': (completed / total * 100) if total > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"Error getting download stats: {e}")
            return {}
    
    async def search_downloads(self, 
                              search_term: str,
                              limit: int = 50) -> List[Dict]:
        """Search downloads by filename, artist, or track name.
        
        Args:
            search_term: Term to search for
            limit: Maximum number of results to return
        
        Returns:
            List of matching download records
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                query = """
                    SELECT * FROM downloads 
                    WHERE filename LIKE ? 
                       OR artist LIKE ? 
                       OR track_name LIKE ?
                       OR search_query LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """
                
                search_pattern = f"%{search_term}%"
                params = [search_pattern, search_pattern, search_pattern, search_pattern, limit]
                
                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
                    
                    downloads = []
                    for row in rows:
                        download = dict(row)
                        if download['created_at']:
                            download['created_at_formatted'] = self._format_timestamp(download['created_at'])
                        if download['completed_at']:
                            download['completed_at_formatted'] = self._format_timestamp(download['completed_at'])
                        downloads.append(download)
                    
                    return downloads
                    
        except Exception as e:
            logger.error(f"Error searching downloads: {e}")
            return []
    
    def _format_timestamp(self, timestamp_str: str) -> str:
        """Format timestamp string for display.
        
        Args:
            timestamp_str: ISO timestamp string
        
        Returns:
            Formatted timestamp string
        """
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return timestamp_str
    
    async def get_count(self, status_filter: str = None, source_filter: str = None) -> int:
        """Get total count of downloads with optional filters.
        
        Args:
            status_filter: Filter by download status
            source_filter: Filter by source type
        
        Returns:
            Total count of matching downloads
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                query = "SELECT COUNT(*) FROM downloads WHERE 1=1"
                params = []
                
                if status_filter:
                    query += " AND download_status = ?"
                    params.append(status_filter)
                
                if source_filter:
                    query += " AND source_type = ?"
                    params.append(source_filter)
                
                async with db.execute(query, params) as cursor:
                    return (await cursor.fetchone())[0]
                    
        except Exception as e:
            logger.error(f"Error getting download count: {e}")
            return 0
