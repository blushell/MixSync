"""Spotify API service for playlist monitoring and track management."""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import logging
from typing import List, Dict, Optional
from config import Config

logger = logging.getLogger(__name__)

class SpotifyService:
    """Manages Spotify API interactions for playlist monitoring."""
    
    def __init__(self):
        """Initialize Spotify service with OAuth."""
        self.sp = None
        self._setup_spotify_client()
    
    def _setup_spotify_client(self):
        """Set up Spotify client with proper authentication."""
        try:
            scope = "playlist-read-private playlist-modify-private playlist-modify-public"
            
            auth_manager = SpotifyOAuth(
                client_id=Config.SPOTIPY_CLIENT_ID,
                client_secret=Config.SPOTIPY_CLIENT_SECRET,
                redirect_uri=Config.SPOTIPY_REDIRECT_URI,
                scope=scope,
                cache_path=".spotify_cache"
            )
            
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            logger.info("Spotify client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Spotify client: {e}")
            raise
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        """Get all tracks from a playlist.
        
        Args:
            playlist_id: Spotify playlist ID (can be full URI or just ID)
        
        Returns:
            List of track dictionaries with simplified information
        """
        try:
            # Extract playlist ID from URI if needed
            if playlist_id.startswith('spotify:playlist:'):
                playlist_id = playlist_id.split(':')[-1]
            elif playlist_id.startswith('https://open.spotify.com/playlist/'):
                playlist_id = playlist_id.split('/')[-1].split('?')[0]
            
            tracks = []
            results = self.sp.playlist_tracks(playlist_id)
            
            while results:
                for item in results['items']:
                    if item['track'] and item['track']['type'] == 'track':
                        track_info = self._extract_track_info(item['track'])
                        track_info['playlist_position'] = len(tracks)
                        tracks.append(track_info)
                
                # Get next batch if available
                if results['next']:
                    results = self.sp.next(results)
                else:
                    break
            
            logger.info(f"Retrieved {len(tracks)} tracks from playlist {playlist_id}")
            return tracks
            
        except Exception as e:
            logger.error(f"Error getting playlist tracks: {e}")
            return []
    
    def _extract_track_info(self, track: Dict) -> Dict:
        """Extract relevant information from a Spotify track object.
        
        Args:
            track: Spotify track object
        
        Returns:
            Simplified track information dictionary
        """
        artists = [artist['name'] for artist in track['artists']]
        
        return {
            'id': track['id'],
            'name': track['name'],
            'artists': artists,
            'artist_string': ', '.join(artists),
            'album': track['album']['name'],
            'duration_ms': track['duration_ms'],
            'explicit': track['explicit'],
            'external_urls': track['external_urls'],
            'preview_url': track['preview_url'],
            'uri': track['uri'],
            'search_query': f"{artists[0]} - {track['name']}" if artists else track['name'],
            'clean_filename': self._create_clean_filename(artists[0] if artists else '', track['name'])
        }
    
    def _create_clean_filename(self, artist: str, track_name: str) -> str:
        """Create a clean filename from artist and track name.
        
        Args:
            artist: Artist name
            track_name: Track name
        
        Returns:
            Clean filename safe for filesystem
        """
        # Combine artist and track name
        filename = f"{artist} - {track_name}" if artist else track_name
        
        # Remove or replace problematic characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        
        # Replace multiple spaces with single space
        filename = ' '.join(filename.split())
        
        # Trim length if needed (filesystem limits)
        if len(filename) > 200:
            filename = filename[:200].strip()
        
        return filename
    
    def remove_track_from_playlist(self, playlist_id: str, track_uri: str, position: Optional[int] = None) -> bool:
        """Remove a track from the playlist.
        
        Args:
            playlist_id: Spotify playlist ID
            track_uri: Track URI to remove
            position: Optional position of track in playlist for more precise removal
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract playlist ID from URI if needed
            if playlist_id.startswith('spotify:playlist:'):
                playlist_id = playlist_id.split(':')[-1]
            
            # Prepare track removal data
            tracks_to_remove = [{"uri": track_uri}]
            if position is not None:
                tracks_to_remove[0]["positions"] = [position]
            
            self.sp.playlist_remove_all_occurrences_of_items(playlist_id, [track_uri])
            logger.info(f"Removed track {track_uri} from playlist {playlist_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing track from playlist: {e}")
            return False
    
    def get_playlist_info(self, playlist_id: str) -> Optional[Dict]:
        """Get basic playlist information.
        
        Args:
            playlist_id: Spotify playlist ID
        
        Returns:
            Playlist information or None if error
        """
        try:
            # Extract playlist ID from URI if needed
            if playlist_id.startswith('spotify:playlist:'):
                playlist_id = playlist_id.split(':')[-1]
            
            playlist = self.sp.playlist(playlist_id)
            return {
                'id': playlist['id'],
                'name': playlist['name'],
                'description': playlist['description'],
                'public': playlist['public'],
                'collaborative': playlist['collaborative'],
                'total_tracks': playlist['tracks']['total'],
                'owner': playlist['owner']['display_name'],
                'external_urls': playlist['external_urls']
            }
            
        except Exception as e:
            logger.error(f"Error getting playlist info: {e}")
            return None
