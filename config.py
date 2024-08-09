# config.py
import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
    SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
    SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # Load from env