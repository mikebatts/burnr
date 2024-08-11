#routes.py


from flask import Blueprint, render_template, redirect, request, url_for, session
import spotipy
import os
from spotipy.oauth2 import SpotifyOAuth
from .openai_api import generate_search_terms
from .spotify_api import create_playlist, search_and_add_tracks_to_playlist

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/callback')
def callback():
    try:
        sp_oauth = SpotifyOAuth(
            client_id=os.getenv("SPOTIPY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
            redirect_uri="http://localhost:5001/callback",
            scope="playlist-modify-public"
        )
        code = request.args.get('code')
        token_info = sp_oauth.get_access_token(code)
        session['token_info'] = token_info
        return redirect(url_for('main.prompt'))
    except Exception as e:
        print(f"Error in callback: {e}")
        return render_template('error.html', message="Failed to authenticate with Spotify.")

@main.route('/prompt', methods=['GET', 'POST'])
def prompt():
    if request.method == 'POST':
        user_prompt = request.form['prompt']
        duration = int(request.form['duration'])

        print(f"Received user prompt: {user_prompt} and duration: {duration} minutes")

        search_terms, track_count = generate_search_terms(user_prompt, duration)
        if not search_terms:
            return render_template('error.html', message="Failed to generate search terms.")

        print(f"Generated search terms: {search_terms} and estimated track count: {track_count}")

        playlist_id = create_playlist([], duration)['id']
        tracks = search_and_add_tracks_to_playlist(playlist_id, search_terms, duration)

        if not tracks:
            return render_template('error.html', message="Failed to add tracks to playlist.")

        return render_template('results.html', playlist={'id': playlist_id, 'title': user_prompt})
    
    return render_template('prompt.html')