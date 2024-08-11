from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import spotipy
import logging
import openai
from spotipy.oauth2 import SpotifyOAuth
from flask_cors import CORS
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, handlers=[
    logging.FileHandler("app.log"),
    logging.StreamHandler()
])
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv('SECRET_KEY')

# Set OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Spotify API credentials
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')

# Initialize Spotify OAuth client
sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                        client_secret=SPOTIPY_CLIENT_SECRET,
                        redirect_uri=SPOTIPY_REDIRECT_URI,
                        scope="user-top-read playlist-modify-public playlist-modify-private")


def get_spotify_client():
    token_info = session.get('token_info')
    if not token_info:
        return None
    
    # Check if token is expired
    if sp_oauth.is_token_expired(token_info):
        logger.info("Token expired, refreshing...")
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
    
    return spotipy.Spotify(auth=token_info['access_token'])


@app.route('/')
def login():
    if session.get('token_info') and session.get('is_authenticated'):
        logger.info("User already authenticated, redirecting to index.")
        return redirect(url_for('index'))
    else:
        logger.info("User not authenticated, rendering login page.")
        authorize_url = sp_oauth.get_authorize_url()
        return render_template('login.html', authorize_url=authorize_url)


@app.route('/callback')
def callback():
    logger.info("Handling Spotify callback...")
    try:
        token_info = sp_oauth.get_access_token(request.args.get('code'))
        logger.info(f"Token Info: {token_info}")
        session['token_info'] = token_info
        session['is_authenticated'] = True
        logger.info("Authentication successful, redirecting to index.")
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"OAuth error: {str(e)}")
        flash("An error occurred during Spotify authentication.")
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/index')
def index():
    if not session.get('is_authenticated'):
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate_playlist():
    if not session.get('is_authenticated'):
        return redirect(url_for('login'))

    mood_prompt = request.form.get('mood')

    if not mood_prompt:
        flash('Please enter a mood or theme for the playlist.')
        return redirect(url_for('index'))

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a music recommendation assistant."},
                {"role": "user", "content": f"Given the mood '{mood_prompt}', suggest relevant genres, artists, and musical characteristics."}
            ],
            max_tokens=150,
            temperature=0.7,
        )

        response_text = completion['choices'][0]['message']['content'].strip()
        search_terms = extract_search_terms(response_text)

        sp = get_spotify_client()
        if not sp:
            flash('Failed to get Spotify client. Please log in again.')
            return redirect(url_for('login'))

        user_top_tracks, user_top_artists = get_user_top_tracks_and_artists(sp)
        track_uris = generate_recommendations(sp, search_terms, user_top_tracks, user_top_artists)

        if not track_uris:
            flash('No tracks found. Try a different mood or theme.')
            return redirect(url_for('index'))

        playlist_name = mood_prompt.lower()
        playlist_id = create_spotify_playlist(sp, playlist_name)
        add_tracks_to_playlist(sp, playlist_id, track_uris)

        return redirect(url_for('show_playlist', playlist_id=playlist_id))

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        flash(f"An error occurred: {str(e)}")
        return redirect(url_for('index'))


@app.route('/playlist/<playlist_id>')
def show_playlist(playlist_id):
    sp = get_spotify_client()
    if not sp:
        flash('Failed to get Spotify client. Please log in again.')
        return redirect(url_for('login'))

    try:
        playlist = sp.playlist(playlist_id)
        return render_template('results.html', playlist=playlist)
    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Spotify API error: {e}")
        flash("Failed to load playlist. Please try again.")
        return redirect(url_for('index'))


# Helper Functions

def extract_search_terms(openai_response):
    terms = {"genres": [], "artists": []}
    lines = openai_response.splitlines()
    for line in lines:
        if "Genres:" in line:
            genres = line.split("Genres:")[1].strip()
            terms["genres"] = [genre.strip() for genre in genres.split(",") if genre]
        elif "Artists:" in line:
            artists = line.split("Artists:")[1].strip()
            terms["artists"] = [artist.strip() for artist in artists.split(",") if artist]
    return terms


def get_user_top_tracks_and_artists(sp):
    top_tracks = sp.current_user_top_tracks(limit=20, time_range='medium_term')
    top_artists = sp.current_user_top_artists(limit=20, time_range='medium_term')

    top_track_ids = [track['id'] for track in top_tracks['items']]
    top_artist_ids = [artist['id'] for artist in top_artists['items']]

    return top_track_ids, top_artist_ids


def generate_recommendations(sp, search_terms, user_top_tracks, user_top_artists, min_songs=100):
    track_uris = set()
    query_limit = 50

    genres = search_terms.get('genres', [])
    artists = search_terms.get('artists', [])

    print(f"Extracted genres from prompt: {genres}")
    print(f"Extracted artists from prompt: {artists}")

    for genre in genres:
        print(f"Searching for tracks in genre: {genre}")
        if len(track_uris) >= min_songs:
            break
        results = sp.search(q=f'genre:"{genre}"', type='track', limit=query_limit)
        for track in results['tracks']['items']:
            if len(track_uris) >= min_songs:
                break
            track_uris.add(track['uri'])

    for artist in artists:
        print(f"Searching for tracks by artist: {artist}")
        if len(track_uris) >= min_songs:
            break
        results = sp.search(q=f'artist:"{artist}"', type='track', limit=query_limit)
        for track in results['tracks']['items']:
            if len(track_uris) >= min_songs:
                break
            track_uris.add(track['uri'])

    if len(track_uris) < min_songs:
        seed_artists = user_top_artists[:5]
        seed_tracks = user_top_tracks[:5]

        total_seeds = len(seed_artists) + len(seed_tracks) + len(genres)
        if total_seeds > 5:
            print(f"Total seeds ({total_seeds}) exceed 5. Adjusting...")
            if len(seed_artists) > 0:
                seed_tracks = seed_tracks[:5 - len(seed_artists)]
                genres = genres[:5 - len(seed_artists) - len(seed_tracks)]
            else:
                genres = genres[:5 - len(seed_tracks)]

        print(f"Adjusted Seed artists: {seed_artists}")
        print(f"Adjusted Seed tracks: {seed_tracks}")
        print(f"Adjusted Seed genres: {genres}")

        try:
            recommendations = sp.recommendations(
                seed_artists=seed_artists if seed_artists else None,
                seed_tracks=seed_tracks if seed_tracks else None,
                seed_genres=genres if genres else None,
                limit=min_songs - len(track_uris)
            )

            for track in recommendations['tracks']:
                track_uris.add(track['uri'])

        except spotipy.SpotifyException as e:
            logger.error(f"Spotify API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")

    return list(track_uris)[:min_songs]


def create_spotify_client(token):
    return spotipy.Spotify(auth=token, requests_timeout=10)


def create_spotify_playlist(sp, name, public=True, collaborative=False):
    user_id = sp.current_user()['id']
    playlist = sp.user_playlist_create(
        user=user_id,
        name=name.lower(),
        public=public,
        description=f"Generated playlist for: {name.lower()} - mixed by burnr",
        collaborative=collaborative
    )
    return playlist['id']


def add_tracks_to_playlist(sp, playlist_id, track_uris):
    sp.playlist_add_items(playlist_id, track_uris)


if __name__ == '__main__':
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.run(debug=False, host='0.0.0.0', port=5001)
