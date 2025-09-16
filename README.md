# 🎵 MixSync - Complete Audio Download Solution

A powerful and modern audio fetcher application with both **automated playlist sync** and **manual web downloads**. Download audio from 1000+ platforms including YouTube, SoundCloud, Bandcamp, and more.

![MixSync](https://img.shields.io/badge/MixSync-v1.0-blue?style=for-the-badge&logo=music) ![Python](https://img.shields.io/badge/Python-3.8+-green?style=for-the-badge&logo=python) ![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

## ✨ Features

### 🎵 Automated Playlist Sync

- **Smart Monitoring**: Watches your Spotify playlist for new tracks automatically
- **Intelligent Downloads**: Uses yt-dlp to find and download high-quality audio from YouTube
- **Clean Filenames**: Uses original Spotify track names for perfect organization
- **Auto-Cleanup**: Removes tracks from playlist after successful download
- **Configurable Polling**: Set your own monitoring interval
- **Resilient**: Handles errors gracefully and maintains download history
- **Smart Polling**: Adaptive monitoring that responds quickly to new tracks

### 🌐 Modern Web Interface

- **Beautiful UI**: Clean, responsive design that works on all devices
- **Real-time Progress**: Watch downloads progress with live updates
- **Multi-Platform**: Support for YouTube, SoundCloud, Bandcamp, and 1000+ sites
- **Custom Filenames**: Override automatic naming with your own choices
- **Download History**: View and manage your downloaded files (configurable display limit)
- **Complete Database**: SQLite database tracks all downloads with search and filtering
- **WebSocket Updates**: Instant feedback without page refreshes

### 🛠️ Advanced Features

- **Filename Cleaning**: Automatically removes YouTube metadata like "[Official Video]"
- **Duplicate Prevention**: Won't re-download the same track twice
- **Error Recovery**: Robust error handling and retry logic
- **Configurable**: Extensive configuration options via environment variables
- **Logging**: Comprehensive logging for debugging and monitoring
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **SQLite Database**: Persistent storage of all download records
- **Advanced Search**: Search downloads by filename, artist, or track name
- **Statistics Dashboard**: Visual overview of download activity and success rates
- **Automatic Metadata Tagging**: Sets artist, title, album, and genre tags on downloaded files
- **Smart Filename Parsing**: Extracts metadata from filenames when Spotify info isn't available

## 🚀 Quick Start

### Option 1: Docker (Recommended)

For containerized deployment with Docker, see the complete **[Docker Guide](DOCKER.md)** which covers:

- GitHub Container Registry usage
- Docker Compose setup
- Local building
- Development environment
- Troubleshooting and maintenance

### Option 2: Traditional Installation

```bash
# Clone the repository
git clone <repository-url>
cd mixsync

# Install dependencies
pip install -r requirements.txt
```

### 2. Spotify API Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Get your `Client ID` and `Client Secret`
4. Add `http://127.0.0.1:8888/callback` to your app's redirect URIs

### 3. Configuration

1. Copy the example environment file:

   ```bash
   cp env_example.txt .env
   ```

2. Edit `.env` with your credentials:

   ```env
   # Spotify API Configuration
   SPOTIPY_CLIENT_ID=your_spotify_client_id_here
   SPOTIPY_CLIENT_SECRET=your_spotify_client_secret_here
   SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback

   # Playlist Configuration
   SPOTIFY_PLAYLIST_ID=your_playlist_id_here

   # Application Settings (Optional - smart polling enabled by default)
   # POLL_INTERVAL_SECONDS=30
   DOWNLOAD_PATH=./downloads
   # MAX_RECENT_DOWNLOADS=10
   # ENABLE_FILE_LOGGING=true

   # Metadata Settings (Optional)
   # ENABLE_METADATA_TAGGING=true
   # DEFAULT_GENRE=Electronic

    # Web Server Configuration (Optional - defaults to localhost:3000)
    # WEB_HOST=localhost
    # WEB_PORT=3000
   ```

### 4. Get Your Playlist ID

1. Open Spotify and go to your playlist
2. Click "Share" → "Copy Spotify URI"
3. The URI looks like: `spotify:playlist:37i9dQZF1DXcBWIGoYBM5M`
4. Use just the ID part (after the last colon) in your `.env` file: `37i9dQZF1DXcBWIGoYBM5M`

### 5. Run the Application

#### Docker

See the **[Docker Guide](DOCKER.md)** for complete Docker setup instructions.

#### Traditional

```bash
python main.py
```

The application will start both services:

- **Web Interface**: Available at `http://localhost:3000`
- **Playlist Sync**: Automatically monitoring your Spotify playlist

## 📖 How It Works

### 🔄 Automated Playlist Sync

1. **Startup**: App connects to Spotify and starts smart monitoring your playlist
2. **Smart Monitoring**: Checks every 30 seconds, with intelligent backoff when idle
3. **Download Process**: For each new track:
   - Creates search query: "Artist - Track Name"
   - Searches YouTube using yt-dlp
   - Downloads the best quality audio available
   - Saves with clean Spotify filename
4. **Cleanup**: Removes successfully downloaded tracks from playlist
5. **Smart Adaptation**: Adjusts monitoring frequency based on activity

### 🧠 Smart Polling System

The playlist sync uses intelligent polling that adapts to your usage:

- **Fast Response**: Checks every 30 seconds by default for immediate detection
- **Activity Detection**: When new tracks are added, maintains fast polling
- **Energy Efficient**: Gradually increases interval (up to 5 minutes) when playlist is idle
- **Auto-Recovery**: Returns to fast polling when activity resumes
- **No Configuration**: Works automatically without needing manual timing setup

### 🌐 Manual Web Downloads

1. **Access**: Visit `http://localhost:3000` in your browser
2. **Input**: Paste any supported media URL
3. **Customize**: Optionally set a custom filename
4. **Download**: Click download and watch real-time progress
5. **Complete**: Files saved to your configured download directory
6. **History**: View complete download history at `/history` with search and filters

### 🗄️ Database & History Features

MixSync includes a comprehensive SQLite database that tracks every download:

- **Complete Records**: Every download attempt is logged with detailed metadata
- **Smart Search**: Search by filename, artist, track name, or any text
- **Advanced Filtering**: Filter by download status (completed/failed/processing) or source (playlist/manual)
- **Statistics Dashboard**: Visual overview showing:
  - Total downloads and success rate
  - Playlist vs manual download breakdown
  - Total file sizes and storage usage
- **Pagination**: Handle thousands of downloads efficiently
- **Real-time Updates**: New downloads appear immediately
- **Historical Data**: Never lose track of what you've downloaded

**Database Location**: `audio_fetcher.db` in project root directory

**Database Schema**: Tracks filename, artist, track name, source URL, file size, download status, timestamps, and more.

### 🏷️ Automatic Metadata Tagging

MixSync automatically sets ID3 tags on all downloaded MP3 files:

- **From Spotify**: When downloading from playlists, uses original Spotify metadata (artist, title, album)
- **From Filenames**: For manual downloads, intelligently extracts artist and title from filenames
- **Smart Cleaning**: Removes YouTube artifacts like "[Official Video]", "(Lyrics)", etc.
- **Smart Album Filtering**: Only sets album field for real albums, skips singles and generic names
- **Configurable Genre**: Set your preferred default genre (default: "Electronic")
- **Automatic BPM Detection**: Uses librosa to analyze and set BPM values on audio files

**Metadata Tags Set:**

- `Artist` - Track artist name
- `Title` - Track title (cleaned of artifacts)
- `Album` - Real album names only (skips singles, EPs, and generic names)
- `Genre` - Configurable default genre
- `BPM` - Automatically detected using audio analysis (configurable)

**Example Metadata:**

```
Artist: "Jessica Audiffred"
Title: "Don't Speak"
Album: (none - single track)
Genre: "Electronic"
BPM: 152
```

**Album Field Logic:**

- ✅ **Sets Album**: "My Great Album", "The Best of 2024", "House Classics Vol. 2"
- ❌ **Skips Album**: "Don't Speak - Single", "Track Name (Single)", "Song EP", "Track Name"

**BPM Detection:**

- ✅ **Automatic Analysis**: Uses librosa's beat tracking algorithm
- ✅ **Smart Processing**: Analyzes 30 seconds from the middle of tracks
- ✅ **Validation**: Only sets BPM values between 60-200 (typical music range)
- ✅ **Fallback Methods**: Uses onset detection if beat tracking fails
- ✅ **Configurable**: Can be disabled via `ENABLE_BPM_DETECTION=false`

## 🎯 Usage Examples

### Adding Songs to Your Playlist

Simply add any track to your monitored Spotify playlist - it will be automatically downloaded and removed from the playlist.

### Manual Downloads

Visit the web interface and paste URLs like:

- `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
- `https://soundcloud.com/artist/track`
- `https://bandcamp.com/track/example`

### Filename Examples

**Spotify-based naming** (playlist sync):

- `Jessica Audiffred - Don't Speak (feat. GG Magree).mp3`
- `ATLiens - BLACK SHEEP (feat. GG MAGREE).mp3`
- `Post Malone - Congratulations ft. Quavo.mp3`

**YouTube title cleaning** (manual downloads):

- `ATLiens - BLACK SHEEP (feat. GG MAGREE) [Official Music Video]` → `ATLiens - BLACK SHEEP (feat. GG MAGREE).mp3`
- `Post Malone - Congratulations ft. Quavo (Official Video)` → `Post Malone - Congratulations ft. Quavo.mp3`

## ⚙️ Configuration Options

| Variable | Description | Default |
| --- | --- | --- |
| `SPOTIPY_CLIENT_ID` | Spotify API Client ID | Required |
| `SPOTIPY_CLIENT_SECRET` | Spotify API Client Secret | Required |
| `SPOTIPY_REDIRECT_URI` | OAuth redirect URI | `http://127.0.0.1:8888/callback` |
| `SPOTIFY_PLAYLIST_ID` | Playlist to monitor | Required |
| `POLL_INTERVAL_SECONDS` | Base polling interval (smart polling adapts) | `30` |
| `DOWNLOAD_PATH` | Where to save downloaded files | `./downloads` |
| `MAX_RECENT_DOWNLOADS` | Number of recent downloads to show in web UI | `10` |
| `ENABLE_FILE_LOGGING` | Enable/disable logging to audio_fetcher.log file | `true` |
| `ENABLE_METADATA_TAGGING` | Enable/disable automatic metadata tagging | `true` |
| `ENABLE_BPM_DETECTION` | Enable/disable automatic BPM analysis | `true` |
| `DEFAULT_GENRE` | Default genre to set for downloaded tracks | `Electronic` |
| `WEB_HOST` | Web server host | `localhost` |
| `WEB_PORT` | Web server port | `3000` |

## 🌐 Supported Platforms

MixSync supports over 1000 platforms through yt-dlp, including:

- **Video**: YouTube, Vimeo, Dailymotion
- **Music**: SoundCloud, Bandcamp, Mixcloud
- **Streaming**: Twitch, Facebook, Instagram
- **And many more**: BBC, CNN, TikTok, Twitter, etc.

## 📁 Project Structure

```
mixsync/
├── main.py                 # Main application entry point
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── env_example.txt        # Environment configuration template
├── services/              # Core services
│   ├── __init__.py
│   ├── spotify_service.py # Spotify API integration
│   ├── download_service.py # yt-dlp download handling
│   └── playlist_sync.py   # Automated sync service
├── web/                   # Web interface
│   ├── app.py            # FastAPI web application
│   ├── templates/        # HTML templates
│   │   └── index.html
│   └── static/           # CSS and JavaScript
│       ├── style.css
│       └── app.js
└── downloads/             # Downloaded files (created automatically)
```

## 🔧 Development

### Prerequisites

- Docker and Docker Compose (for containerized development)
- OR Python 3.8+ and FFmpeg (for traditional development)
- Git

### Setting Up Development Environment

#### Docker Development (Recommended)

See the **[Docker Guide](DOCKER.md)** for complete Docker development setup with live reload, debugging, and troubleshooting.

#### Traditional Development

```bash
# Clone and setup
git clone <repository-url>
cd mixsync
pip install -r requirements.txt

# Copy configuration
cp env_example.txt .env
# Edit .env with your credentials

# Run in development mode
python main.py
```

### API Endpoints

The web interface provides several API endpoints:

- `GET /` - Main web interface
- `POST /download` - Start a download
- `GET /api/downloads` - List downloaded files
- `GET /api/supported-sites` - Get supported platforms
- `GET /api/download-history` - Get paginated download history with search/filters
- `GET /api/download-stats` - Get download statistics
- `GET /health` - Health check
- `WebSocket /ws` - Real-time updates

## 🐛 Troubleshooting

### Common Issues

**"Configuration errors found"**

- Make sure you've copied `env_example.txt` to `.env`
- Fill in all required Spotify API credentials
- Check that your playlist ID is correct

**"Could not authenticate with Spotify"**

- Verify your Client ID and Client Secret
- Ensure the redirect URI matches your Spotify app settings
- Check that your Spotify app has the correct permissions

**"Download failed"**

- Ensure FFmpeg is installed and available in PATH
- Check that the URL is from a supported platform
- Some content may be geo-restricted or unavailable

**"Web interface not accessible"**

- Check that port 3000 is not in use by another application
- Try changing `WEB_PORT` in your `.env` file (add `WEB_PORT=8000` for example)
- Ensure your firewall allows connections to the port
- For Docker: Check that the port mapping is correct (`-p 3000:3000`)

**Docker Issues**

For Docker-specific troubleshooting, see the **[Docker Guide](DOCKER.md)** which covers common container issues, networking, permissions, and debugging.

### Logs

Check the application logs for detailed error information:

#### Docker Logs

See the **[Docker Guide](DOCKER.md)** for complete Docker logging instructions.

#### Traditional Logs

- Console output shows real-time status
- `audio_fetcher.log` contains detailed logs (if file logging is enabled)
- Web browser console shows frontend errors
- Set `ENABLE_FILE_LOGGING=false` in `.env` to disable log file creation

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## ⚠️ Legal Notice

This tool is for personal use only. Please respect copyright laws and the terms of service of the platforms you download from. Only download content you have the right to download.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📞 Support

If you encounter any issues or have questions:

1. Check the troubleshooting section above
2. Look through existing issues on GitHub
3. Create a new issue with detailed information about your problem

---

**Made with ❤️ for music lovers everywhere**
