import spotipy
from spotipy.oauth2 import SpotifyOAuth

def create_playlist(tracks, duration):
    try:
        # Initialize Spotify client
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth())
        
        # Get current user ID
        user_id = sp.current_user()["id"]
        
        # Create a new playlist
        playlist = sp.user_playlist_create(user_id, "Generated Playlist", public=False)
        
        # Add tracks to the playlist
        sp.playlist_add_items(playlist["id"], tracks)
        
        return playlist
    except Exception as e:
        print(f"Error creating playlist: {e}")
        return None