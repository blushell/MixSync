"""Metadata service for setting audio file tags."""

import logging
import re
from pathlib import Path
from typing import Optional, Dict
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TBPM, TALB, TYER, TCON, TPE2
from mutagen import File as MutagenFile

logger = logging.getLogger(__name__)

class MetadataService:
    """Handles setting metadata tags on downloaded audio files."""
    
    def __init__(self):
        """Initialize metadata service."""
        pass
    
    async def set_metadata(self, 
                          file_path: str,
                          artist: str = None,
                          title: str = None,
                          album: str = None,
                          year: str = None,
                          genre: str = None,
                          bpm: int = None) -> bool:
        """Set metadata tags on an audio file.
        
        Args:
            file_path: Path to the audio file
            artist: Artist name
            title: Track title
            album: Album name
            year: Release year
            genre: Music genre
            bpm: Beats per minute
        
        Returns:
            True if metadata was set successfully, False otherwise
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"File does not exist: {file_path}")
                return False
            
            # Load the audio file
            audiofile = MutagenFile(str(file_path))
            
            if audiofile is None:
                logger.error(f"Could not load audio file: {file_path}")
                return False
            
            # Handle MP3 files specifically
            if isinstance(audiofile, MP3):
                return self._set_mp3_metadata(audiofile, artist, title, album, year, genre, bpm)
            else:
                # For other formats, use generic tags
                return self._set_generic_metadata(audiofile, artist, title, album, year, genre, bpm)
                
        except Exception as e:
            logger.error(f"Error setting metadata for {file_path}: {e}")
            return False
    
    def _set_mp3_metadata(self, audiofile: MP3, artist: str, title: str, 
                         album: str, year: str, genre: str, bpm: int) -> bool:
        """Set metadata for MP3 files using ID3 tags.
        
        Args:
            audiofile: MP3 file object
            artist: Artist name
            title: Track title
            album: Album name
            year: Release year
            genre: Music genre
            bpm: Beats per minute
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Initialize ID3 tags if they don't exist
            if audiofile.tags is None:
                audiofile.add_tags()
            
            # Set title
            if title:
                audiofile.tags.add(TIT2(encoding=3, text=title))
            
            # Set artist
            if artist:
                audiofile.tags.add(TPE1(encoding=3, text=artist))
                # Also set album artist to the same value
                audiofile.tags.add(TPE2(encoding=3, text=artist))
            
            # Set album (only if it's a valid album name)
            if album and self._is_valid_album(album, title):
                audiofile.tags.add(TALB(encoding=3, text=album))
            
            # Set year
            if year:
                audiofile.tags.add(TYER(encoding=3, text=str(year)))
            
            # Set genre
            if genre:
                audiofile.tags.add(TCON(encoding=3, text=genre))
            
            # Set BPM
            if bpm and isinstance(bpm, (int, float)):
                audiofile.tags.add(TBPM(encoding=3, text=str(int(bpm))))
            
            # Save the tags
            audiofile.save()
            logger.info(f"Successfully set MP3 metadata: {artist} - {title}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting MP3 metadata: {e}")
            return False
    
    def _set_generic_metadata(self, audiofile, artist: str, title: str,
                            album: str, year: str, genre: str, bpm: int) -> bool:
        """Set metadata for non-MP3 audio files using generic tags.
        
        Args:
            audiofile: Audio file object
            artist: Artist name
            title: Track title
            album: Album name
            year: Release year
            genre: Music genre
            bpm: Beats per minute
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Set title
            if title:
                audiofile['TITLE'] = title
            
            # Set artist
            if artist:
                audiofile['ARTIST'] = artist
                audiofile['ALBUMARTIST'] = artist
            
            # Set album (only if it's a valid album name)
            if album and self._is_valid_album(album, title):
                audiofile['ALBUM'] = album
            
            # Set year/date
            if year:
                audiofile['DATE'] = str(year)
            
            # Set genre
            if genre:
                audiofile['GENRE'] = genre
            
            # Set BPM
            if bpm and isinstance(bpm, (int, float)):
                audiofile['BPM'] = str(int(bpm))
            
            # Save the tags
            audiofile.save()
            logger.info(f"Successfully set generic metadata: {artist} - {title}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting generic metadata: {e}")
            return False
    
    def extract_metadata_from_filename(self, filename: str) -> Dict[str, str]:
        """Extract artist and title from filename.
        
        Args:
            filename: The filename to parse
        
        Returns:
            Dictionary with extracted metadata
        """
        try:
            # Remove file extension
            name_without_ext = Path(filename).stem
            
            # Common patterns for "Artist - Title"
            patterns = [
                r'^(.+?)\s*-\s*(.+?)$',  # "Artist - Title"
                r'^(.+?)\s*–\s*(.+?)$',  # "Artist – Title" (em dash)
                r'^(.+?)\s*—\s*(.+?)$',  # "Artist — Title" (em dash)
            ]
            
            for pattern in patterns:
                match = re.match(pattern, name_without_ext.strip())
                if match:
                    artist = match.group(1).strip()
                    title = match.group(2).strip()
                    
                    # Clean up common artifacts
                    title = self._clean_title(title)
                    artist = self._clean_artist(artist)
                    
                    return {
                        'artist': artist,
                        'title': title,
                        'album': '',  # We don't typically extract album from filename
                        'year': '',
                        'genre': '',
                        'bpm': None
                    }
            
            # If no pattern matches, treat the whole filename as title
            return {
                'artist': '',
                'title': self._clean_title(name_without_ext),
                'album': '',
                'year': '',
                'genre': '',
                'bpm': None
            }
            
        except Exception as e:
            logger.error(f"Error extracting metadata from filename {filename}: {e}")
            return {
                'artist': '',
                'title': filename,
                'album': '',
                'year': '',
                'genre': '',
                'bpm': None
            }
    
    def _clean_title(self, title: str) -> str:
        """Clean up title by removing common artifacts.
        
        Args:
            title: Title to clean
        
        Returns:
            Cleaned title
        """
        # Remove common YouTube/video artifacts
        artifacts = [
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
            r'\[Explicit\]',
            r'\(Explicit\)',
        ]
        
        cleaned_title = title
        for artifact in artifacts:
            cleaned_title = re.sub(artifact, '', cleaned_title, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        cleaned_title = ' '.join(cleaned_title.split())
        
        return cleaned_title.strip()
    
    def _clean_artist(self, artist: str) -> str:
        """Clean up artist name by removing common artifacts.
        
        Args:
            artist: Artist name to clean
        
        Returns:
            Cleaned artist name
        """
        # Remove common prefixes/suffixes
        artist = artist.strip()
        
        # Remove "Official" or "VEVO" suffixes
        artist = re.sub(r'\s*(Official|VEVO|Music)$', '', artist, flags=re.IGNORECASE)
        
        return artist.strip()
    
    def _is_valid_album(self, album: str, title: str) -> bool:
        """Check if the album name is a real album (not a single or generic name).
        
        Args:
            album: Album name to validate
            title: Track title for comparison
        
        Returns:
            True if it's a valid album name, False otherwise
        """
        if not album or not album.strip():
            return False
        
        album_lower = album.lower().strip()
        title_lower = title.lower().strip() if title else ""
        
        # Skip if album contains single/EP indicators
        single_indicators = [
            '- single', ' single', 'single -', 'single)',
            '- ep', ' ep', 'ep -', 'ep)',
            '(single)', '[single]',
            '(ep)', '[ep]'
        ]
        
        for indicator in single_indicators:
            if indicator in album_lower:
                return False
        
        # Skip if album is just the track title
        if title_lower and album_lower == title_lower:
            return False
        
        # Skip if album is track title + common suffixes
        if title_lower:
            title_variants = [
                f"{title_lower} - single",
                f"{title_lower} single",
                f"{title_lower} (single)",
                f"{title_lower} [single]",
                f"{title_lower} - ep",
                f"{title_lower} ep",
                f"{title_lower} (ep)",
                f"{title_lower} [ep]"
            ]
            if album_lower in title_variants:
                return False
        
        return True
    
    async def estimate_bpm(self, file_path: str) -> Optional[int]:
        """Estimate BPM of an audio file using librosa.
        
        Args:
            file_path: Path to the audio file
        
        Returns:
            Estimated BPM or None if detection fails
        """
        try:
            import librosa
            import numpy as np
            
            logger.info(f"Analyzing BPM for {file_path}...")
            
            # Load audio file with error handling
            # Use a shorter duration for faster processing (30 seconds from the middle)
            try:
                y, sr = librosa.load(file_path, duration=30, offset=30)
            except Exception as load_error:
                logger.warning(f"Failed to load audio file {file_path}: {load_error}")
                return None
            
            # Detect tempo/BPM with multiple methods for robustness
            try:
                # Primary method: beat tracking
                tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=512)
                
                # If tempo seems unreasonable, try onset detection
                if not (60 <= tempo <= 200):
                    onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
                    if len(onset_frames) > 1:
                        # Calculate average time between onsets
                        onset_times = librosa.onset.onset_times_to_samples(onset_frames, sr=sr)
                        avg_interval = np.mean(np.diff(onset_times)) / sr
                        tempo = 60.0 / avg_interval if avg_interval > 0 else tempo
                
            except Exception as beat_error:
                logger.warning(f"Beat tracking failed: {beat_error}")
                return None
            
            # Round to nearest integer
            bpm = int(round(tempo))
            
            # Validate BPM range (typical music is 60-200 BPM)
            if 60 <= bpm <= 200:
                logger.info(f"Detected BPM: {bpm} for {Path(file_path).name}")
                return bpm
            else:
                logger.warning(f"BPM {bpm} outside normal range (60-200), discarding")
                return None
            
        except ImportError:
            logger.warning("librosa not installed - BPM detection disabled")
            return None
        except Exception as e:
            logger.warning(f"BPM detection failed for {file_path}: {e}")
            return None
    
    def get_file_metadata(self, file_path: str) -> Dict:
        """Get existing metadata from an audio file.
        
        Args:
            file_path: Path to the audio file
        
        Returns:
            Dictionary with existing metadata
        """
        try:
            audiofile = MutagenFile(str(file_path))
            
            if audiofile is None:
                return {}
            
            metadata = {
                'artist': '',
                'title': '',
                'album': '',
                'year': '',
                'genre': '',
                'bpm': None,
                'duration': getattr(audiofile.info, 'length', 0)
            }
            
            # Handle MP3 files
            if isinstance(audiofile, MP3) and audiofile.tags:
                metadata['artist'] = str(audiofile.tags.get('TPE1', [''])[0])
                metadata['title'] = str(audiofile.tags.get('TIT2', [''])[0])
                metadata['album'] = str(audiofile.tags.get('TALB', [''])[0])
                metadata['year'] = str(audiofile.tags.get('TYER', [''])[0])
                metadata['genre'] = str(audiofile.tags.get('TCON', [''])[0])
                bpm_tag = audiofile.tags.get('TBPM')
                if bpm_tag:
                    try:
                        metadata['bpm'] = int(str(bpm_tag[0]))
                    except (ValueError, IndexError):
                        pass
            else:
                # Handle other formats
                metadata['artist'] = audiofile.get('ARTIST', [''])[0] if audiofile.get('ARTIST') else ''
                metadata['title'] = audiofile.get('TITLE', [''])[0] if audiofile.get('TITLE') else ''
                metadata['album'] = audiofile.get('ALBUM', [''])[0] if audiofile.get('ALBUM') else ''
                metadata['year'] = audiofile.get('DATE', [''])[0] if audiofile.get('DATE') else ''
                metadata['genre'] = audiofile.get('GENRE', [''])[0] if audiofile.get('GENRE') else ''
                bpm_tag = audiofile.get('BPM')
                if bpm_tag:
                    try:
                        metadata['bpm'] = int(bpm_tag[0])
                    except (ValueError, IndexError):
                        pass
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting metadata from {file_path}: {e}")
            return {}
