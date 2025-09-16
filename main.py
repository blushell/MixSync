"""Main application entry point for MixSync."""

import asyncio
import logging
import sys
import signal
from typing import Optional
from pathlib import Path

import uvicorn
from colorama import init, Fore, Style
init(autoreset=True)

from config import Config
from services.playlist_sync import PlaylistSyncService
from services.database_service import DatabaseService
from web.app import app, database_service

# Setup logging
def setup_logging():
    """Setup logging configuration based on config settings."""
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # Add file handler only if enabled in config
    if Config.ENABLE_FILE_LOGGING:
        handlers.append(logging.FileHandler('audio_fetcher.log'))
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

setup_logging()

logger = logging.getLogger(__name__)

class AudioFetcherApp:
    """Main application class that coordinates all services."""
    
    def __init__(self):
        """Initialize the application."""
        self.playlist_sync = None
        self.web_server_task = None
        self.running = False
        
    def print_banner(self):
        """Print application banner."""
        banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════╗
║                 {Fore.YELLOW}MixSync{Fore.CYAN}                    ║
║        Complete Audio Download Solution          ║
╚══════════════════════════════════════════════════╝{Style.RESET_ALL}

{Fore.GREEN}🎵 Playlist Sync:{Style.RESET_ALL} Automated downloads from Spotify playlists
{Fore.BLUE}🌐 Web Interface:{Style.RESET_ALL} Manual downloads at http://localhost:{Config.WEB_PORT}
{Fore.YELLOW}📁 Download Path:{Style.RESET_ALL} {Config.DOWNLOAD_PATH}
"""
        print(banner)
    
    def validate_config(self) -> bool:
        """Validate configuration and setup.
        
        Returns:
            True if configuration is valid
        """
        errors = Config.validate()
        
        if errors:
            print(f"{Fore.RED}Configuration errors found:{Style.RESET_ALL}")
            for error in errors:
                print(f"  {Fore.RED}✗{Style.RESET_ALL} {error}")
            print(f"\n{Fore.YELLOW}Please check your .env file and fix the above errors.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Copy env_example.txt to .env and fill in your credentials.{Style.RESET_ALL}")
            return False
        
        # Setup directories and database
        try:
            Config.setup_directories()
            print(f"{Fore.GREEN}✓{Style.RESET_ALL} Configuration valid")
            print(f"{Fore.GREEN}✓{Style.RESET_ALL} Download directory ready: {Config.DOWNLOAD_PATH}")
            return True
        except Exception as e:
            print(f"{Fore.RED}✗{Style.RESET_ALL} Error setting up directories: {e}")
            return False
    
    async def start_web_server(self):
        """Start the web server."""
        try:
            logger.info(f"Starting web server on {Config.WEB_HOST}:{Config.WEB_PORT}")
            print(f"{Fore.BLUE}🌐 Web Interface:{Style.RESET_ALL} http://localhost:{Config.WEB_PORT}")
            
            config = uvicorn.Config(
                app,
                host=Config.WEB_HOST,
                port=Config.WEB_PORT,
                log_level="info",
                access_log=False
            )
            server = uvicorn.Server(config)
            await server.serve()
            
        except Exception as e:
            logger.error(f"Web server error: {e}")
            print(f"{Fore.RED}✗{Style.RESET_ALL} Web server failed to start: {e}")
    
    async def start_playlist_sync(self):
        """Start the playlist sync service."""
        try:
            print(f"{Fore.GREEN}🎵 Playlist Sync:{Style.RESET_ALL} Starting automated monitoring...")
            print(f"   Smart polling: {Config.POLL_INTERVAL_SECONDS}s (adapts to activity)")
            print(f"   Playlist ID: {Config.SPOTIFY_PLAYLIST_ID}")
            
            self.playlist_sync = PlaylistSyncService()
            await self.playlist_sync.start_monitoring()
            
        except Exception as e:
            logger.error(f"Playlist sync error: {e}")
            print(f"{Fore.RED}✗{Style.RESET_ALL} Playlist sync failed: {e}")
    
    async def run(self):
        """Run the main application."""
        self.running = True
        
        # Print banner and validate config
        self.print_banner()
        
        if not self.validate_config():
            return 1
        
        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Initialize database
            print(f"{Fore.BLUE}🗄️  Database:{Style.RESET_ALL} Initializing SQLite database...")
            await database_service.initialize()
            print(f"{Fore.GREEN}✓{Style.RESET_ALL} Database ready")
            
            # Start services concurrently
            tasks = []
            
            # Start web server
            web_task = asyncio.create_task(self.start_web_server())
            tasks.append(web_task)
            
            # Start playlist sync
            sync_task = asyncio.create_task(self.start_playlist_sync())
            tasks.append(sync_task)
            
            print(f"\n{Fore.GREEN}✨ MixSync is running!{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Press Ctrl+C to stop{Style.RESET_ALL}\n")
            
            # Wait for any task to complete (usually due to error or shutdown)
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            
            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            return 0
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            return 0
        except Exception as e:
            logger.error(f"Application error: {e}")
            print(f"{Fore.RED}✗{Style.RESET_ALL} Application error: {e}")
            return 1
        finally:
            self.stop()
    
    def stop(self):
        """Stop all services."""
        if not self.running:
            return
        
        self.running = False
        print(f"\n{Fore.YELLOW}🛑 Shutting down MixSync...{Style.RESET_ALL}")
        
        if self.playlist_sync:
            self.playlist_sync.stop_monitoring()
            print(f"{Fore.GREEN}✓{Style.RESET_ALL} Playlist sync stopped")
        
        print(f"{Fore.GREEN}✓{Style.RESET_ALL} MixSync shutdown complete")

def main():
    """Main entry point."""
    try:
        app = AudioFetcherApp()
        return asyncio.run(app.run())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Interrupted by user{Style.RESET_ALL}")
        return 0
    except Exception as e:
        print(f"{Fore.RED}Fatal error: {e}{Style.RESET_ALL}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
