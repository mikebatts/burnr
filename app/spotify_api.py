#spotify_api.py

import spotipy
from spotipy.oauth2 import SpotifyOAuth

def create_playlist(tracks, duration):
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth())
        user_id = sp.current_user()["id"]

        playlist = sp.user_playlist_create(user_id, "Generated Playlist", public=False)
        return playlist
    except Exception as e:
        print(f"Error creating playlist: {e}")
        return None

def search_and_add_tracks_to_playlist(playlist_id, search_terms, duration):
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth())
        total_duration_ms = 0
        tracks = []
        track_limit = duration // 3  # Estimate number of tracks based on duration

        for term in search_terms.split(","):
            results = sp.search(q=term, limit=track_limit)
            for item in results['tracks']['items']:
                tracks.append(item['uri'])
                total_duration_ms += item['duration_ms']
                if len(tracks) >= track_limit or total_duration_ms >= (duration * 60000):
                    break
            if len(tracks) >= track_limit or total_duration_ms >= (duration * 60000):
                break

        if tracks:
            sp.playlist_add_items(playlist_id, tracks)

        return tracks
    except Exception as e:
        print(f"Error adding tracks to playlist: {e}")
        return None