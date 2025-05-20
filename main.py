import os
import argparse
import pandas as pd
from datetime import datetime

from youtube_api import YouTubeAPI
from music_categorizer import MusicCategorizer
from config import CACHE_DIR

def save_results(df, output_format="csv"):
    """
    Save categorized music results to a file.
    
    Args:
        df (pd.DataFrame): DataFrame with categorized songs
        output_format (str): Output format (csv, json, or excel)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if output_format == "csv":
        output_file = f"categorized_music_{timestamp}.csv"
        df.to_csv(output_file, index=False)
    elif output_format == "json":
        output_file = f"categorized_music_{timestamp}.json"
        df.to_json(output_file, orient="records", indent=4)
    elif output_format == "excel":
        output_file = f"categorized_music_{timestamp}.xlsx"
        df.to_excel(output_file, index=False)
    else:
        print(f"Unsupported output format: {output_format}")
        return None
    
    print(f"Results saved to {output_file}")
    return output_file

def main():
    """Main function to run the YouTube Music Categorizer application."""
    parser = argparse.ArgumentParser(description="YouTube Music Categorizer and Sorter")
    
    parser.add_argument("--query", "-q", type=str, help="Search query for YouTube Music")
    parser.add_argument("--playlist", "-p", type=str, help="YouTube playlist ID to analyze")
    parser.add_argument("--liked", "-l", action="store_true", help="Fetch and analyze your liked videos (requires OAuth)")
    parser.add_argument("--max-results", "-m", type=int, default=50, help="Maximum number of results to fetch")
    parser.add_argument("--sort-by", "-s", type=str, default="view_count", 
                        help="Attribute to sort by (view_count, like_count, published_at, etc.)")
    parser.add_argument("--ascending", "-a", action="store_true", help="Sort in ascending order")
    parser.add_argument("--genre-filter", "-g", type=str, help="Filter by specific genre")
    parser.add_argument("--mood-filter", "-md", type=str, help="Filter by specific mood")
    parser.add_argument("--year-filter", "-y", type=int, help="Filter by specific release year")
    parser.add_argument("--output", "-o", type=str, default="csv", choices=["csv", "json", "excel"],
                        help="Output format (csv, json, or excel)")
    parser.add_argument("--visualize", "-v", action="store_true", help="Create visualizations of the results")
    
    args = parser.parse_args()
    
    # Determine if we need OAuth
    use_oauth = args.liked
    
    # Initialize APIs and categorizer
    youtube_api = YouTubeAPI(use_oauth=use_oauth)
    categorizer = MusicCategorizer()
    
    songs_data = []
    
    # Get music data
    if args.liked:
        print("Fetching your liked videos...")
        songs_data = youtube_api.get_liked_videos(args.max_results)
    elif args.query:
        print(f"Searching for '{args.query}' on YouTube Music...")
        songs_data = youtube_api.search_music(args.query, args.max_results)
    elif args.playlist:
        print(f"Getting playlist items for playlist ID '{args.playlist}'...")
        playlist_items = youtube_api.get_playlist_items(args.playlist, args.max_results)
        
        # Get detailed info for each playlist item
        songs_data = []
        for item in playlist_items:
            video_details = youtube_api.get_video_details(item['id'])
            item.update(video_details)
            songs_data.append(item)
    else:
        print("Please provide a search query, playlist ID, or use the --liked option.")
        parser.print_help()
        return
    
    if not songs_data:
        print("No music data found.")
        return
    
    print(f"Found {len(songs_data)} songs. Categorizing...")
    
    # Categorize songs
    df = categorizer.categorize_songs(songs_data)
    
    # Apply filters
    if args.genre_filter:
        df = categorizer.filter_by_attribute(df, "genre", args.genre_filter)
        print(f"Filtered to {len(df)} songs with genre '{args.genre_filter}'")
    
    if args.mood_filter:
        df = categorizer.filter_by_attribute(df, "mood", args.mood_filter)
        print(f"Filtered to {len(df)} songs with mood '{args.mood_filter}'")
    
    if args.year_filter:
        df = categorizer.filter_by_attribute(df, "release_year", args.year_filter)
        print(f"Filtered to {len(df)} songs from year {args.year_filter}")
    
    # Sort results
    if args.sort_by:
        df = categorizer.sort_by_attribute(df, args.sort_by, args.ascending)
        print(f"Sorted by '{args.sort_by}' ({'ascending' if args.ascending else 'descending'})")
    
    # Create visualizations
    if args.visualize:
        print("Creating visualizations...")
        categorizer.visualize_genres(df)
        categorizer.visualize_moods(df)
        categorizer.visualize_years(df)
        print("Visualizations saved as PNG files.")
    
    # Save results
    save_results(df, args.output)
    
    # Print summary
    print("\nSummary:")
    print(f"Total songs: {len(df)}")
    print("\nGenre distribution:")
    print(df['genre'].value_counts().to_string())
    print("\nMood distribution:")
    print(df['mood'].value_counts().to_string())

if __name__ == "__main__":
    main()
