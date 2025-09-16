# MixSync - Complete Audio Download Solution

A complete audio fetcher application with both **automated playlist sync** and **manual web downloads**.

## Features

### 🎵 Playlist Sync (Automated)

- Watches a Spotify playlist for new tracks
- Automatically downloads audio using yt-dlp (YouTube search)
- Removes tracks from playlist after successful download
- Configurable polling interval
- Uses clean Spotify track names for files

### 🌐 Web UI (Manual Downloads)

- Beautiful, modern web interface at `http://localhost:8000`
- Download audio from any supported platform (YouTube, SoundCloud, etc.)
- Custom filename support
- Real-time download progress
- Mobile-responsive design

### 2. Spotify API Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Get your `Client ID` and `Client Secret`
4. Add `http://127.0.0.1:8888/callback` to your app's redirect URIs

### 3. Environment Configuration

1. Copy the example environment file:

   ```bash
   cp env_example.txt .env
   ```

2. Edit `.env` with your credentials:
   ```
   SPOTIPY_CLIENT_ID=your_spotify_client_id
   SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
   SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
   SPOTIFY_PLAYLIST_ID=spotify:playlist:your_playlist_id
   POLL_INTERVAL_MINUTES=10
   DOWNLOAD_PATH=./downloads
   ```

### 4. Get Your Playlist ID

1. Open Spotify and go to your playlist
2. Click "Share" → "Copy Spotify URI"
3. The URI looks like: `spotify:playlist:37i9dQZF1DXcBWIGoYBM5M`
4. Use the full URI in your `.env` file

## How It Works

### 🔄 Automated Playlist Sync

1. **Startup**: App connects to Spotify and starts monitoring
2. **Monitoring**: Every `POLL_INTERVAL_MINUTES`, checks for new tracks
3. **Download**: For each new track:
   - Formats search query: "Artist - Track Name"
   - Searches YouTube using yt-dlp
   - Downloads the first result and saves with clean Spotify filename
4. **Cleanup**: Removes successfully downloaded tracks from playlist
5. **Repeat**: Continues monitoring for new tracks

### 🌐 Manual Web Downloads

1. **Access**: Visit `http://localhost:8000` in your browser
2. **Input**: Paste any supported media URL (YouTube, SoundCloud, etc.)
3. **Customize**: Optionally set a custom filename
4. **Download**: Click download and watch real-time progress
5. **Complete**: Files saved to your configured download directory

### Filename Sources

**Primary (Spotify-based)**: For playlist sync, files are named using the original Spotify track information:

- Format: `Artist - Track Name`
- Examples:
  - `Jessica Audiffred - Don't Speak (feat. GG Magree)`
  - `ATLiens - BLACK SHEEP (feat. GG MAGREE)`
  - `Post Malone - Congratulations ft. Quavo`

**Fallback (YouTube title cleaning)**: For manual downloads or when Spotify info isn't available:

- Automatically removes YouTube video metadata like "[Official Music Video]", "(Official Audio)", etc.
- Examples:
  - `ATLiens - BLACK SHEEP (feat. GG MAGREE) [Official Music Video]` → `ATLiens - BLACK SHEEP (feat. GG MAGREE)`
  - `Post Malone - Congratulations ft. Quavo (Official Video)` → `Post Malone - Congratulations ft. Quavo`
