import re
import json
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter

class MusicCategorizer:
    def __init__(self):
        """Initialize the music categorizer."""
        # Common genre keywords for classification
        self.genre_keywords = {
            'pop': ['pop', 'dance pop', 'electropop'],
            'rock': ['rock', 'alternative', 'indie', 'punk', 'metal', 'grunge'],
            'hip hop': ['hip hop', 'rap', 'trap', 'drill', 'r&b', 'rnb'],
            'electronic': ['edm', 'electronic', 'house', 'techno', 'dubstep', 'trance', 'drum and bass'],
            'country': ['country', 'folk', 'bluegrass', 'americana'],
            'jazz': ['jazz', 'blues', 'soul', 'funk'],
            'classical': ['classical', 'orchestra', 'piano', 'symphony', 'concerto'],
            'latin': ['latin', 'reggaeton', 'salsa', 'bachata', 'cumbia'],
            'k-pop': ['k-pop', 'kpop', 'k pop'],
            'j-pop': ['j-pop', 'jpop', 'j pop'],
        }
        
        # Mood classification keywords
        self.mood_keywords = {
            'happy': ['happy', 'upbeat', 'uplifting', 'cheerful', 'fun', 'feel good', 'party'],
            'sad': ['sad', 'melancholy', 'heartbreak', 'emotional', 'tearful', 'ballad'],
            'relaxing': ['chill', 'relax', 'calm', 'peaceful', 'ambient', 'sleep', 'study'],
            'energetic': ['energetic', 'workout', 'fitness', 'gym', 'hype', 'energy', 'pump'],
            'romantic': ['love', 'romantic', 'romance', 'wedding', 'valentine'],
        }
        
        # Year regex pattern
        self.year_pattern = r'\b(19[0-9]{2}|20[0-2][0-9])\b'
    
    def categorize_songs(self, songs_data):
        """
        Categorize a list of songs based on genre, mood, year, etc.
        
        Args:
            songs_data (list): List of song dictionaries
            
        Returns:
            pd.DataFrame: DataFrame with categorized songs
        """
        categorized_songs = []
        
        for song in songs_data:
            # Extract song metadata
            title = song.get('title', '').lower()
            description = song.get('description', '').lower()
            tags = [tag.lower() for tag in song.get('tags', [])]
            
            # Combined text for analysis
            text = f"{title} {description} {' '.join(tags)}"
            
            # Detect genre
            genre = self._detect_genre(text, tags)
            
            # Detect mood
            mood = self._detect_mood(text, tags)
            
            # Extract year
            year = self._extract_year(text)
            
            # Add categorized info to the song
            categorized_song = song.copy()
            categorized_song.update({
                'genre': genre,
                'mood': mood,
                'release_year': year
            })
            
            categorized_songs.append(categorized_song)
        
        # Convert to DataFrame
        df = pd.DataFrame(categorized_songs)
        return df
    
    def _detect_genre(self, text, tags):
        """
        Detect genre from text and tags.
        
        Args:
            text (str): Combined text for analysis
            tags (list): List of video tags
            
        Returns:
            str: Detected genre or 'unknown'
        """
        for genre, keywords in self.genre_keywords.items():
            for keyword in keywords:
                if keyword in text or keyword in tags:
                    return genre
        
        return 'unknown'
    
    def _detect_mood(self, text, tags):
        """
        Detect mood from text and tags.
        
        Args:
            text (str): Combined text for analysis
            tags (list): List of video tags
            
        Returns:
            str: Detected mood or 'other'
        """
        for mood, keywords in self.mood_keywords.items():
            for keyword in keywords:
                if keyword in text or keyword in tags:
                    return mood
        
        return 'other'
    
    def _extract_year(self, text):
        """
        Extract year from text.
        
        Args:
            text (str): Text to extract year from
            
        Returns:
            int or None: Extracted year or None
        """
        year_match = re.search(self.year_pattern, text)
        
        if year_match:
            return int(year_match.group(1))
            
        return None
    
    def sort_by_attribute(self, df, attribute, ascending=True):
        """
        Sort songs by a specific attribute.
        
        Args:
            df (pd.DataFrame): DataFrame with categorized songs
            attribute (str): Attribute to sort by
            ascending (bool): Sort in ascending order
            
        Returns:
            pd.DataFrame: Sorted DataFrame
        """
        if attribute in df.columns:
            return df.sort_values(by=attribute, ascending=ascending)
        else:
            print(f"Attribute '{attribute}' not found.")
            return df
    
    def filter_by_attribute(self, df, attribute, value):
        """
        Filter songs by a specific attribute value.
        
        Args:
            df (pd.DataFrame): DataFrame with categorized songs
            attribute (str): Attribute to filter by
            value: Value to filter for
            
        Returns:
            pd.DataFrame: Filtered DataFrame
        """
        if attribute in df.columns:
            return df[df[attribute] == value]
        else:
            print(f"Attribute '{attribute}' not found.")
            return df
    
    def visualize_genres(self, df):
        """
        Create a visualization of song genres.
        
        Args:
            df (pd.DataFrame): DataFrame with categorized songs
        """
        plt.figure(figsize=(12, 6))
        df['genre'].value_counts().plot(kind='bar', color='skyblue')
        plt.title('Songs by Genre')
        plt.xlabel('Genre')
        plt.ylabel('Count')
        plt.tight_layout()
        plt.savefig('genre_distribution.png')
        plt.close()
        
    def visualize_moods(self, df):
        """
        Create a visualization of song moods.
        
        Args:
            df (pd.DataFrame): DataFrame with categorized songs
        """
        plt.figure(figsize=(10, 6))
        df['mood'].value_counts().plot(kind='pie', autopct='%1.1f%%')
        plt.title('Songs by Mood')
        plt.tight_layout()
        plt.savefig('mood_distribution.png')
        plt.close()
        
    def visualize_years(self, df):
        """
        Create a visualization of song release years.
        
        Args:
            df (pd.DataFrame): DataFrame with categorized songs
        """
        years_data = df['release_year'].dropna()
        
        if len(years_data) > 0:
            plt.figure(figsize=(14, 6))
            years_data.value_counts().sort_index().plot(kind='line', marker='o')
            plt.title('Songs by Release Year')
            plt.xlabel('Year')
            plt.ylabel('Count')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig('year_distribution.png')
            plt.close()