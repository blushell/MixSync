"""Audio download service using yt-dlp with filename cleaning."""

import yt_dlp
import asyncio
import logging
import re
from pathlib import Path
from typing import Optional, Dict, Callable
from config import Config
from .metadata_service import MetadataService

logger = logging.getLogger(__name__)

class DownloadService:
    """Manages audio downloads using yt-dlp."""
    
    def __init__(self):
        """Initialize download service."""
        self.download_path = Config.DOWNLOAD_PATH
        self.download_path.mkdir(parents=True, exist_ok=True)
        self.metadata_service = MetadataService()
    
    def _get_ydl_opts(self, custom_filename: Optional[str] = None, progress_hook: Optional[Callable] = None) -> Dict:
        """Get yt-dlp options for audio download.
        
        Args:
            custom_filename: Custom filename (without extension)
            progress_hook: Optional progress callback function
        
        Returns:
            yt-dlp options dictionary
        """
        opts = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'audioformat': 'mp3',
            'audioquality': '192K',
            'outtmpl': str(self.download_path / '%(title)s.%(ext)s'),
            'noplaylist': True,
            'ignoreerrors': True,
            'no_warnings': False,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        
        if custom_filename:
            clean_filename = self._sanitize_filename(custom_filename)
            opts['outtmpl'] = str(self.download_path / f'{clean_filename}.%(ext)s')
        
        if progress_hook:
            opts['progress_hooks'] = [progress_hook]
        
        return opts
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility.
        
        Args:
            filename: Original filename
        
        Returns:
            Sanitized filename
        """
        # Remove problematic characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        
        # Remove YouTube-specific metadata patterns
        youtube_patterns = [
            r'\[Official\s*(Music\s*)?Video\]',
            r'\(Official\s*(Music\s*)?Video\)',
            r'\[Official\s*Audio\]',
            r'\(Official\s*Audio\)',
            r'\[Lyrics?\]',
            r'\(Lyrics?\)',
            r'\[HD\]',
            r'\(HD\)',
            r'\[4K\]',
            r'\(4K\)',
            r'\[Music\s*Video\]',
            r'\(Music\s*Video\)',
            r'\[Visualizer\]',
            r'\(Visualizer\)',
            r'\[Lyric\s*Video\]',
            r'\(Lyric\s*Video\)',
        ]
        
        for pattern in youtube_patterns:
            filename = re.sub(pattern, '', filename, flags=re.IGNORECASE)
        
        # Clean up extra spaces and trim
        filename = ' '.join(filename.split()).strip()
        
        # Limit length
        if len(filename) > 200:
            filename = filename[:200].strip()
        
        return filename
    
    async def download_audio(self, url: str, custom_filename: Optional[str] = None, 
                           progress_callback: Optional[Callable] = None) -> Dict:
        """Download audio from URL.
        
        Args:
            url: URL to download from
            custom_filename: Custom filename (without extension)
            progress_callback: Optional progress callback function
        
        Returns:
            Dictionary with download result information
        """
        try:
            logger.info(f"Starting download from: {url}")
            
            # Prepare progress tracking
            download_info = {
                'status': 'starting',
                'url': url,
                'filename': None,
                'filepath': None,
                'progress': 0,
                'speed': None,
                'eta': None,
                'error': None
            }
            
            def progress_hook(d):
                if d['status'] == 'downloading':
                    if 'total_bytes' in d:
                        download_info['progress'] = (d['downloaded_bytes'] / d['total_bytes']) * 100
                    elif 'total_bytes_estimate' in d:
                        download_info['progress'] = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                    
                    download_info['speed'] = d.get('speed')
                    download_info['eta'] = d.get('eta')
                    download_info['status'] = 'downloading'
                    
                    if progress_callback:
                        progress_callback(download_info.copy())
                
                elif d['status'] == 'finished':
                    download_info['status'] = 'processing'
                    download_info['progress'] = 100
                    download_info['filepath'] = d['filename']
                    
                    if progress_callback:
                        progress_callback(download_info.copy())
            
            # Get yt-dlp options
            ydl_opts = self._get_ydl_opts(custom_filename, progress_hook)
            
            # Run download in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._download_with_ydlp, 
                url, 
                ydl_opts, 
                download_info
            )
            
            # If download was successful, set metadata (if enabled)
            if result['status'] == 'completed' and result.get('filepath') and Config.ENABLE_METADATA_TAGGING:
                try:
                    await self.set_file_metadata(result['filepath'])
                except Exception as e:
                    logger.warning(f"Failed to set metadata after download: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return {
                'status': 'error',
                'url': url,
                'error': str(e),
                'filename': None,
                'filepath': None,
                'progress': 0
            }
    
    def _download_with_ydlp(self, url: str, ydl_opts: Dict, download_info: Dict) -> Dict:
        """Execute yt-dlp download in a separate thread.
        
        Args:
            url: URL to download
            ydl_opts: yt-dlp options
            download_info: Download information dictionary to update
        
        Returns:
            Updated download information
        """
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown')
                
                # Clean the title
                clean_title = self._sanitize_filename(title)
                download_info['filename'] = f"{clean_title}.mp3"
                
                # Download the audio
                ydl.download([url])
                
                # Find the downloaded file
                expected_path = self.download_path / download_info['filename']
                if expected_path.exists():
                    download_info['filepath'] = str(expected_path)
                else:
                    # Search for mp3 files with similar names
                    possible_files = list(self.download_path.glob("*.mp3"))
                    if possible_files:
                        # Get the most recently created file
                        latest_file = max(possible_files, key=lambda p: p.stat().st_mtime)
                        download_info['filepath'] = str(latest_file)
                        download_info['filename'] = latest_file.name
                
                download_info['status'] = 'completed'
                download_info['progress'] = 100
                logger.info(f"Download completed: {download_info['filename']}")
                
        except Exception as e:
            download_info['status'] = 'error'
            download_info['error'] = str(e)
            logger.error(f"yt-dlp download error: {e}")
        
        return download_info
    
    async def set_file_metadata(self, 
                               file_path: str,
                               artist: str = None,
                               title: str = None,
                               album: str = None,
                               year: str = None,
                               genre: str = None,
                               bpm: int = None) -> bool:
        """Set metadata tags on a downloaded file.
        
        Args:
            file_path: Path to the downloaded file
            artist: Artist name
            title: Track title
            album: Album name
            year: Release year
            genre: Music genre
            bpm: Beats per minute
        
        Returns:
            True if metadata was set successfully
        """
        try:
            # If no metadata provided, try to extract from filename
            if not artist and not title:
                extracted = self.metadata_service.extract_metadata_from_filename(Path(file_path).name)
                artist = artist or extracted.get('artist')
                title = title or extracted.get('title')
                album = album or extracted.get('album')
                year = year or extracted.get('year')
                genre = genre or extracted.get('genre')
                bpm = bpm or extracted.get('bpm')
            
            # Set default genre if not provided
            if not genre:
                genre = Config.DEFAULT_GENRE
            
            # Estimate BPM if not provided and BPM detection is enabled
            if bpm is None and Config.ENABLE_BPM_DETECTION:
                try:
                    bpm = await self.metadata_service.estimate_bpm(file_path)
                except Exception as e:
                    logger.warning(f"BPM estimation failed: {e}")
                    bpm = None
            
            # Set metadata using the metadata service
            success = await self.metadata_service.set_metadata(
                file_path=file_path,
                artist=artist,
                title=title,
                album=album,
                year=year,
                genre=genre,
                bpm=bpm
            )
            
            if success:
                logger.info(f"Metadata set for {Path(file_path).name}: {artist} - {title}")
            else:
                logger.warning(f"Failed to set metadata for {Path(file_path).name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error setting metadata for {file_path}: {e}")
            return False
    
    async def search_and_download(self, search_query: str, custom_filename: Optional[str] = None,
                                progress_callback: Optional[Callable] = None) -> Dict:
        """Search YouTube and download the first result.
        
        Args:
            search_query: Search query string
            custom_filename: Custom filename (without extension)
            progress_callback: Optional progress callback function
        
        Returns:
            Dictionary with download result information
        """
        try:
            logger.info(f"Searching for: {search_query}")
            
            # Search for the track on YouTube
            search_url = f"ytsearch1:{search_query}"
            
            return await self.download_audio(
                search_url, 
                custom_filename, 
                progress_callback
            )
            
        except Exception as e:
            logger.error(f"Search and download failed: {e}")
            return {
                'status': 'error',
                'url': search_url,
                'error': str(e),
                'filename': None,
                'filepath': None,
                'progress': 0
            }
    
    def get_supported_sites(self) -> list:
        """Get list of supported sites from yt-dlp.
        
        Returns:
            List of supported extractor names
        """
        try:
            # Use the module-level function instead of instance method
            from yt_dlp.extractor import list_extractors
            extractors = list_extractors()
            return [extractor.IE_NAME for extractor in extractors if hasattr(extractor, 'IE_NAME')]
        except Exception as e:
            logger.error(f"Error getting supported sites: {e}")
            # Return a fallback list of popular platforms
            return ['youtube', 'soundcloud', 'bandcamp', 'vimeo', 'dailymotion', 'mixcloud']
