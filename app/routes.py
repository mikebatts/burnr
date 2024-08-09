from flask import Blueprint, render_template, redirect, request, url_for, session
import spotipy
import os
from spotipy.oauth2 import SpotifyOAuth
from .openai_api import generate_prompt_response
from .spotify_api import create_playlist

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/callback')
def callback():
    sp_oauth = SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri="http://localhost:5001/callback",
        scope="playlist-modify-private"  # Add required scopes here

    )
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    # Store token_info securely (e.g., in session)
    session['token_info'] = token_info
    return redirect(url_for('main.prompt'))

@main.route('/prompt', methods=['GET', 'POST'])
def prompt():
    if request.method == 'POST':
        user_prompt = request.form['prompt']
        duration = request.form['duration']
        playlist_info = generate_prompt_response(user_prompt)
        playlist = create_playlist(playlist_info, duration)
        return render_template('results.html', playlist=playlist)
    return render_template('prompt.html')