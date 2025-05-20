import os
import json
import pickle
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from config import (
    YOUTUBE_API_KEY, 
    YOUTUBE_CLIENT_ID, 
    YOUTUBE_CLIENT_SECRET,
    OAUTH_REDIRECT_URI,
    OAUTH_SCOPES,
    MAX_RESULTS, 
    CACHE_DIR, 
    TOKEN_FILE
)

class YouTubeAPI:
    def __init__(self, use_oauth=False):
        """
        Initialize YouTube API client.
        
        Args:
            use_oauth (bool): Whether to use OAuth 2.0 for authentication
        """
        self.use_oauth = use_oauth
        
        if use_oauth:
            # Use OAuth 2.0 credentials
            credentials = self._get_oauth_credentials()
            self.youtube = build('youtube', 'v3', credentials=credentials)
        else:
            # Use API key
            self.youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
    
    def _get_oauth_credentials(self):
        """
        Get OAuth 2.0 credentials.
        
        Returns:
            google.oauth2.credentials.Credentials: OAuth 2.0 credentials
        """
        credentials = None
        
        # Check if token file exists
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                credentials = pickle.load(token)
        
        # If credentials are not valid, refresh or get new ones
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                # Create client_secrets.json file for OAuth flow
                client_config = {
                    "installed": {
                        "client_id": YOUTUBE_CLIENT_ID,
                        "client_secret": YOUTUBE_CLIENT_SECRET,
                        "redirect_uris": [OAUTH_REDIRECT_URI],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token"
                    }
                }
                
                # Save client secrets to a temporary file
                with open('client_secrets.json', 'w') as f:
                    json.dump(client_config, f)
                
                # Start OAuth flow
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secrets.json', OAUTH_SCOPES)
                credentials = flow.run_local_server(port=8080)
                
                # Clean up temporary file
                os.remove('client_secrets.json')
                
                # Save credentials for future use
                with open(TOKEN_FILE, 'wb') as token:
                    pickle.dump(credentials, token)
        
        return credentials
    
    def search_music(self, query, max_results=MAX_RESULTS, cache_duration=24):
        """
        Search for music on YouTube Music.
        
        Args:
            query (str): Search query
            max_results (int): Maximum number of results to return
            cache_duration (int): Cache duration in hours
            
        Returns:
            list: List of music items
        """
        # Create a cache key based on the query
        cache_key = f"music_search_{query.replace(' ', '_')}.pkl"
        cache_path = os.path.join(CACHE_DIR, cache_key)
        
        # Check if we have a cached result that's not expired
        if os.path.exists(cache_path):
            with open(cache_path, 'rb') as f:
                cached_data = pickle.load(f)
                if cached_data['timestamp'] > datetime.now() - timedelta(hours=cache_duration):
                    print(f"Using cached results for '{query}'")
                    return cached_data['results']
        
        try:
            # Search for music content
            search_response = self.youtube.search().list(
                q=query,
                part="id,snippet",
                maxResults=max_results,
                type="video",
                videoCategoryId="10",  # Music category
                topicId="/m/04rlf",    # Music topic
                fields="items(id(videoId),snippet(title,description,publishedAt,channelTitle,thumbnails))"
            ).execute()
            
            results = []
            
            # Process the search results
            for item in search_response.get('items', []):
                video_id = item['id']['videoId']
                
                # Get additional video details
                video_details = self.get_video_details(video_id)
                
                # Combine search and detail information
                music_item = {
                    'id': video_id,
                    'title': item['snippet']['title'],
                    'channel': item['snippet']['channelTitle'],
                    'published_at': item['snippet']['publishedAt'],
                    'description': item['snippet']['description'],
                    'thumbnail': item['snippet']['thumbnails']['high']['url'] if 'high' in item['snippet']['thumbnails'] else None,
                    'duration': video_details.get('duration'),
                    'view_count': video_details.get('view_count'),
                    'like_count': video_details.get('like_count'),
                    'tags': video_details.get('tags', []),
                    'category': video_details.get('category')
                }
                
                results.append(music_item)
            
            # Cache the results
            with open(cache_path, 'wb') as f:
                pickle.dump({
                    'timestamp': datetime.now(),
                    'results': results
                }, f)
                
            return results
            
        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred: {e.content}")
            return []
    
    def get_video_details(self, video_id):
        """
        Get detailed information about a YouTube video.
        
        Args:
            video_id (str): YouTube video ID
            
        Returns:
            dict: Video details
        """
        try:
            # Get video details
            video_response = self.youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=video_id
            ).execute()
            
            if not video_response['items']:
                return {}
                
            video = video_response['items'][0]
            snippet = video['snippet']
            content_details = video['contentDetails']
            statistics = video['statistics']
            
            # Format duration from ISO 8601 format (PT#M#S)
            duration_str = content_details['duration']
            duration = self._parse_duration(duration_str)
            
            return {
                'duration': duration,
                'view_count': int(statistics.get('viewCount', 0)),
                'like_count': int(statistics.get('likeCount', 0)) if 'likeCount' in statistics else None,
                'tags': snippet.get('tags', []),
                'category': snippet.get('categoryId')
            }
            
        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred: {e.content}")
            return {}
    
    def get_playlist_items(self, playlist_id, max_results=MAX_RESULTS):
        """
        Get items from a YouTube playlist.
        
        Args:
            playlist_id (str): YouTube playlist ID
            max_results (int): Maximum number of results to return
            
        Returns:
            list: List of playlist items
        """
        try:
            # Get playlist items
            playlist_response = self.youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=max_results
            ).execute()
            
            videos = []
            for item in playlist_response.get('items', []):
                video_id = item['contentDetails']['videoId']
                videos.append({
                    'id': video_id,
                    'title': item['snippet']['title'],
                    'position': item['snippet']['position'],
                    'published_at': item['snippet']['publishedAt'],
                    'channel': item['snippet']['channelTitle']
                })
                
            return videos
            
        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred: {e.content}")
            return []
            
    def get_liked_videos(self, max_results=MAX_RESULTS):
        """
        Get the user's liked videos.
        
        Args:
            max_results (int): Maximum number of results to return
            
        Returns:
            list: List of liked videos
        """
        if not self.use_oauth:
            print("Error: OAuth authentication is required to access liked videos.")
            print("Please initialize YouTubeAPI with use_oauth=True")
            return []
            
        try:
            # Get the 'liked videos' playlist ID (it's a special playlist)
            channels_response = self.youtube.channels().list(
                part="contentDetails",
                mine=True
            ).execute()
            
            if not channels_response['items']:
                print("No channel found for authenticated user.")
                return []
                
            # Get the 'liked videos' playlist ID
            liked_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['likes']
            
            # Get the playlist items
            videos = []
            next_page_token = None
            
            while len(videos) < max_results:
                # Get playlist items
                playlist_items_response = self.youtube.playlistItems().list(
                    part="snippet,contentDetails",
                    playlistId=liked_playlist_id,
                    maxResults=min(50, max_results - len(videos)),
                    pageToken=next_page_token
                ).execute()
                
                # Process items
                for item in playlist_items_response.get('items', []):
                    if 'videoId' not in item['contentDetails']:
                        continue  # Skip deleted videos
                        
                    video_id = item['contentDetails']['videoId']
                    
                    # Get additional video details
                    video_details = self.get_video_details(video_id)
                    
                    # Combine playlist item info with video details
                    video_item = {
                        'id': video_id,
                        'title': item['snippet']['title'],
                        'channel': item['snippet']['channelTitle'],
                        'published_at': item['snippet']['publishedAt'],
                        'description': item['snippet'].get('description', ''),
                        'thumbnail': item['snippet']['thumbnails']['high']['url'] if 'high' in item['snippet']['thumbnails'] else None,
                        'duration': video_details.get('duration'),
                        'view_count': video_details.get('view_count'),
                        'like_count': video_details.get('like_count'),
                        'tags': video_details.get('tags', []),
                        'category': video_details.get('category')
                    }
                    
                    videos.append(video_item)
                
                # Check if there are more pages
                next_page_token = playlist_items_response.get('nextPageToken')
                
                if not next_page_token or len(videos) >= max_results:
                    break
            
            return videos
            
        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred: {e.content}")
            return []
            
    def _parse_duration(self, duration_str):
        """
        Convert ISO 8601 duration format to seconds.
        
        Args:
            duration_str (str): Duration in ISO 8601 format (PT#M#S)
            
        Returns:
            int: Duration in seconds
        """
        duration_str = duration_str[2:]  # Remove 'PT'
        seconds = 0
        
        # Handle hours
        if 'H' in duration_str:
            hours, duration_str = duration_str.split('H')
            seconds += int(hours) * 3600
        
        # Handle minutes
        if 'M' in duration_str:
            minutes, duration_str = duration_str.split('M')
            seconds += int(minutes) * 60
        
        # Handle seconds
        if 'S' in duration_str:
            s = duration_str.split('S')[0]
            seconds += int(s)
            
        return seconds