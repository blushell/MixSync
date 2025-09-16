"""Automated playlist sync service with polling."""

import asyncio
import logging
from typing import Set, List, Dict, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path

from services.spotify_service import SpotifyService
from services.download_service import DownloadService
from services.database_service import DatabaseService
from config import Config

logger = logging.getLogger(__name__)

class PlaylistSyncService:
    """Manages automated playlist synchronization."""
    
    def __init__(self):
        """Initialize playlist sync service."""
        self.spotify_service = SpotifyService()
        self.download_service = DownloadService()
        self.database_service = DatabaseService()
        self.running = False
        self.last_check = None
        self.processed_tracks = self._load_processed_tracks()
        self.stats = {
            'total_downloads': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'tracks_removed': 0,
            'last_sync': None
        }
        
    def _load_processed_tracks(self) -> Set[str]:
        """Load previously processed track IDs from cache file.
        
        Returns:
            Set of processed track IDs
        """
        cache_file = Path('.processed_tracks.json')
        try:
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('processed_tracks', []))
        except Exception as e:
            logger.warning(f"Could not load processed tracks cache: {e}")
        
        return set()
    
    def _save_processed_tracks(self):
        """Save processed track IDs to cache file."""
        cache_file = Path('.processed_tracks.json')
        try:
            data = {
                'processed_tracks': list(self.processed_tracks),
                'last_updated': datetime.now().isoformat(),
                'stats': self.stats
            }
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save processed tracks cache: {e}")
    
    async def start_monitoring(self):
        """Start monitoring the playlist for new tracks with smart polling."""
        if self.running:
            logger.warning("Playlist monitoring is already running")
            return
        
        self.running = True
        logger.info(f"Starting smart playlist monitoring (checking every {Config.POLL_INTERVAL_SECONDS} seconds)...")
        
        # Initial check
        await self._check_playlist()
        
        # Smart polling with exponential backoff when no changes
        current_interval = Config.POLL_INTERVAL_SECONDS
        max_interval = 300  # Max 5 minutes
        no_change_count = 0
        
        while self.running:
            try:
                await asyncio.sleep(current_interval)
                if not self.running:  # Check if still running after sleep
                    break
                
                # Store previous track count for change detection
                previous_processed_count = len(self.processed_tracks)
                
                # Check for changes
                await self._check_playlist()
                
                # Adjust polling interval based on activity
                current_processed_count = len(self.processed_tracks)
                if current_processed_count > previous_processed_count:
                    # New tracks were processed, reset to fast polling
                    current_interval = Config.POLL_INTERVAL_SECONDS
                    no_change_count = 0
                    logger.info("New activity detected, maintaining fast polling")
                else:
                    # No new tracks, gradually increase interval
                    no_change_count += 1
                    if no_change_count >= 3:  # After 3 checks with no changes
                        current_interval = min(current_interval * 1.5, max_interval)
                        logger.debug(f"No changes detected, increasing interval to {current_interval:.0f} seconds")
                
            except asyncio.CancelledError:
                logger.info("Playlist monitoring cancelled")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                # Reset to default interval on error
                current_interval = Config.POLL_INTERVAL_SECONDS
                await asyncio.sleep(30)
    
    def stop_monitoring(self):
        """Stop monitoring the playlist."""
        if not self.running:
            return
        
        self.running = False
        logger.info("Stopping playlist monitoring...")
        self._save_processed_tracks()
    
    async def _check_playlist(self):
        """Check playlist for new tracks and process them."""
        try:
            logger.info("Checking playlist for new tracks...")
            self.last_check = datetime.now()
            
            # Get playlist info
            playlist_info = self.spotify_service.get_playlist_info(Config.SPOTIFY_PLAYLIST_ID)
            if not playlist_info:
                logger.error("Could not get playlist information")
                return
            
            logger.info(f"Monitoring playlist: {playlist_info['name']} "
                       f"(Total tracks: {playlist_info['total_tracks']})")
            
            # Get current tracks
            tracks = self.spotify_service.get_playlist_tracks(Config.SPOTIFY_PLAYLIST_ID)
            if not tracks:
                logger.info("No tracks found in playlist")
                return
            
            # Find new tracks (not previously processed)
            new_tracks = [track for track in tracks if track['id'] not in self.processed_tracks]
            
            if not new_tracks:
                logger.info("No new tracks found")
                return
            
            logger.info(f"Found {len(new_tracks)} new tracks to download")
            
            # Process new tracks
            for track in new_tracks:
                if not self.running:  # Check if we should stop
                    break
                    
                await self._process_track(track)
                # Small delay between downloads to be respectful
                await asyncio.sleep(2)
            
            self.stats['last_sync'] = datetime.now().isoformat()
            self._save_processed_tracks()
            
        except Exception as e:
            logger.error(f"Error checking playlist: {e}")
    
    async def _process_track(self, track: Dict):
        """Process a single track: download and optionally remove from playlist.
        
        Args:
            track: Track information dictionary
        """
        track_id = track['id']
        track_name = f"{track['artist_string']} - {track['name']}"
        
        try:
            logger.info(f"Processing track: {track_name}")
            self.stats['total_downloads'] += 1
            
            # Add download record to database
            db_id = await self.database_service.add_download(
                filename=track['clean_filename'],
                original_url=None,  # No direct URL for Spotify tracks
                source_type='playlist',
                artist=track['artist_string'],
                track_name=track['name'],
                search_query=track['search_query'],
                spotify_track_id=track['id']
            )
            
            # Download the track
            download_result = await self.download_service.search_and_download(
                search_query=track['search_query'],
                custom_filename=track['clean_filename']
            )
            
            # If download was successful, set metadata with Spotify info (if enabled)
            if (download_result['status'] == 'completed' and 
                download_result.get('filepath') and 
                Config.ENABLE_METADATA_TAGGING):
                try:
                    await self.download_service.set_file_metadata(
                        file_path=download_result['filepath'],
                        artist=track['artist_string'],
                        title=track['name'],
                        album=track['album'],
                        genre=Config.DEFAULT_GENRE
                    )
                except Exception as e:
                    logger.warning(f"Failed to set Spotify metadata: {e}")
            
            if download_result['status'] == 'completed':
                logger.info(f"Successfully downloaded: {track_name}")
                self.stats['successful_downloads'] += 1
                
                # Update database with success
                if download_result.get('filepath'):
                    file_path = Path(download_result['filepath'])
                    file_size = file_path.stat().st_size if file_path.exists() else 0
                    
                    await self.database_service.update_download_success(
                        download_id=db_id,
                        file_path=str(file_path),
                        file_size=file_size
                    )
                
                # Mark as processed
                self.processed_tracks.add(track_id)
                
                # Remove from playlist after successful download
                removed = self.spotify_service.remove_track_from_playlist(
                    playlist_id=Config.SPOTIFY_PLAYLIST_ID,
                    track_uri=track['uri'],
                    position=track.get('playlist_position')
                )
                
                if removed:
                    logger.info(f"Removed track from playlist: {track_name}")
                    self.stats['tracks_removed'] += 1
                else:
                    logger.warning(f"Could not remove track from playlist: {track_name}")
                
            else:
                logger.error(f"Download failed for {track_name}: {download_result.get('error', 'Unknown error')}")
                self.stats['failed_downloads'] += 1
                
                # Update database with failure
                await self.database_service.update_download_failed(
                    download_id=db_id,
                    error_message=download_result.get('error', 'Unknown error')
                )
                
                # Still mark as processed to avoid retrying failed downloads
                # You can modify this behavior if you want to retry failed downloads
                self.processed_tracks.add(track_id)
                
        except Exception as e:
            logger.error(f"Error processing track {track_name}: {e}")
            self.stats['failed_downloads'] += 1
            
            # Update database with failure if db_id exists
            if 'db_id' in locals():
                try:
                    await self.database_service.update_download_failed(
                        download_id=db_id,
                        error_message=str(e)
                    )
                except Exception as db_error:
                    logger.error(f"Failed to update database for error case: {db_error}")
                    
            # Mark as processed to avoid infinite retries
            self.processed_tracks.add(track_id)
    
    def get_status(self) -> Dict:
        """Get current status of the playlist sync service.
        
        Returns:
            Status dictionary
        """
        return {
            'running': self.running,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'processed_tracks_count': len(self.processed_tracks),
            'poll_interval_seconds': Config.POLL_INTERVAL_SECONDS,
            'playlist_id': Config.SPOTIFY_PLAYLIST_ID,
            'download_path': str(Config.DOWNLOAD_PATH),
            'stats': self.stats.copy()
        }
    
    async def manual_sync(self) -> Dict:
        """Manually trigger a playlist sync.
        
        Returns:
            Sync result dictionary
        """
        if self.running:
            return {
                'status': 'error',
                'message': 'Automatic monitoring is running. Stop it first to run manual sync.'
            }
        
        try:
            logger.info("Starting manual playlist sync...")
            await self._check_playlist()
            
            return {
                'status': 'completed',
                'message': 'Manual sync completed successfully',
                'stats': self.stats.copy()
            }
            
        except Exception as e:
            logger.error(f"Manual sync failed: {e}")
            return {
                'status': 'error',
                'message': f'Manual sync failed: {str(e)}'
            }
    
    def reset_processed_tracks(self):
        """Reset the processed tracks cache (will reprocess all tracks in playlist)."""
        self.processed_tracks.clear()
        self._save_processed_tracks()
        logger.info("Reset processed tracks cache")
    
    def get_playlist_preview(self) -> Optional[Dict]:
        """Get a preview of the current playlist without processing.
        
        Returns:
            Playlist preview with track information
        """
        try:
            playlist_info = self.spotify_service.get_playlist_info(Config.SPOTIFY_PLAYLIST_ID)
            if not playlist_info:
                return None
            
            tracks = self.spotify_service.get_playlist_tracks(Config.SPOTIFY_PLAYLIST_ID)
            
            new_tracks = [
                {
                    'id': track['id'],
                    'name': track['name'],
                    'artist': track['artist_string'],
                    'search_query': track['search_query'],
                    'clean_filename': track['clean_filename'],
                    'processed': track['id'] in self.processed_tracks
                }
                for track in tracks
            ]
            
            return {
                'playlist_info': playlist_info,
                'tracks': new_tracks,
                'new_tracks_count': len([t for t in new_tracks if not t['processed']]),
                'total_tracks': len(new_tracks)
            }
            
        except Exception as e:
            logger.error(f"Error getting playlist preview: {e}")
            return None
