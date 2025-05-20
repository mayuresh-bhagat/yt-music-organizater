import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# YouTube Data API credentials
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")

# OAuth 2.0 settings
OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8080")
OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

# Optional: Spotify API credentials for additional music metadata
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Application settings
MAX_RESULTS = 50  # Number of results to fetch per API call
CACHE_DIR = "./cache"  # Directory to cache API responses
TOKEN_FILE = "token.pickle"  # File to store OAuth 2.0 token