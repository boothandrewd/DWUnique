""" app/__init__.py
"""
import json
import os
import re
from urllib.parse import urlencode

import requests
from flask import Flask, redirect, render_template, request, session, make_response
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from pymongo import MongoClient

# Set up flask
server = Flask(__name__)
server.config.from_pyfile('config.py')

# Get env vars
# From app config
APP_URL = server.config['APP_URL']
SPOTIPY_REDIRECT_URI = server.config['SPOTIPY_REDIRECT_URI']
# From env
MONGODB_URI = os.environ['MONGODB_URI']
SPOTIPY_CLIENT_ID = os.environ['SPOTIPY_CLIENT_ID']
SPOTIPY_CLIENT_SECRET = os.environ['SPOTIPY_CLIENT_SECRET']
DWUNIQUE_REFRESH_TOKEN = os.environ['DWUNIQUE_REFRESH_TOKEN']
TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
TWILIO_NUMBER = os.environ['TWILIO_NUMBER']

# Last import
from app.PlaylistManager import PlaylistManager

# Set up mongo
users = MongoClient(MONGODB_URI).get_default_database().users


# Helper function
def parse_playlist_resource(resource):
    return resource.split(':' if resource.startswith('spotify') else '/')[-1]

# Auth constants
USER_AUTH_PARAMS = {
    'response_type': 'code',
    'redirect_uri': SPOTIPY_REDIRECT_URI,
    'scope': 'user-read-email',
    'state': 'user-auth',
    'client_id': SPOTIPY_CLIENT_ID
}


# Routes
@server.route('/')
def index():
    # If session started, go to playlists
    if 'user_id' in session:
        return redirect('/playlists')

    # If valid cookie on client, go to playlists
    user_id = request.cookies.get('user_id')
    if user_id is not None:
        user_record = users.find_one({'user_id': user_id})
        if user_record is not None:
            return redirect('/playlists')

    # Sign in otherwise
    return redirect('/signin')


@server.route('/signin', methods=['GET', 'POST'])
def signin():
    # Submit or render
    if request.method == 'POST':
        return redirect(f'https://accounts.spotify.com/authorize/?{urlencode(USER_AUTH_PARAMS)}')
    return render_template('signin.html')


@server.route('/spotify-auth-callback')
def spotify_auth_callback():
    # Use authorization token to get access token
    auth_token = request.args['code']
    access_response = requests.post('https://accounts.spotify.com/api/token', data={
        'grant_type': 'authorization_code',
        'code': str(auth_token),
        'redirect_uri': SPOTIPY_REDIRECT_URI,
        'client_id': SPOTIPY_CLIENT_ID,
        'client_secret': SPOTIPY_CLIENT_SECRET
    })
    access_data = json.loads(access_response.text)
    access_token = access_data['access_token']
    refresh_token = access_data['refresh_token']

    # Start sessiong with spotify
    auth_spotify = spotipy.Spotify(
        auth=access_token,
        client_credentials_manager=SpotifyClientCredentials(
            SPOTIPY_CLIENT_ID,
            SPOTIPY_CLIENT_SECRET
        )
    )

    # Get user data
    current_user = auth_spotify.current_user()
    user_id = current_user['id']

    # Check if in database
    user_record = users.find_one({'user_id': user_id})

    # If not, create record
    if user_record is None:
        users.insert_one({
            'user_id': user_id,
            'user_display_name': current_user['display_name'],
            'user_email': current_user['email'],
            'email_update_setting': False,
            'refresh_token': refresh_token,
            'mobile_number': '',
            'mobile_update_setting': True,
            'dw_id': '',
            'dwu_id': '',
            'dwh_id': '',
            'last_update': ''
        })

    # Set client-side memory structures
    session['user_id'] = user_id
    resp = make_response(redirect('/playlists'))
    resp.set_cookie('user_id', user_id)

    return resp


@server.route('/connect', methods=['GET', 'POST'])
def connect():
    # Sign in if not signed in
    if 'user_id' not in session:
        return redirect('/signin')

    if request.method == 'POST':
        # Get submitted playlist id
        playlist_id = parse_playlist_resource(request.form['pl-resource'])
        mobile_number = re.sub(r'\D', '', request.form['mobile-number'])

        # Verify it actually exists on Spotify servers
        try:
            spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
                SPOTIPY_CLIENT_ID,
                SPOTIPY_CLIENT_SECRET
            ))
            spotify.user_playlist('spotify', playlist_id)
        except spotipy.client.SpotifyException:
            return render_template('connect.html', error='Please enter a valid URL, URI, or ID')

        # Update database with playlist id
        users.update_one({'user_id': session['user_id']}, {
            '$set': {
                'dw_id': playlist_id,
                'mobile_number': mobile_number
            }
        })

        # Redirect user to their playlists
        return redirect('/playlists')

    return render_template('connect.html', error='')


@server.route('/playlists')
def playlists():
    # Sign in if not signed in
    if 'user_id' not in session:
        return redirect('/signin')

    # Get user data, redirect to connect if no DW connected
    user_record = users.find_one({'user_id': session['user_id']})
    if user_record['dw_id'] == '':
        return redirect('/connect')

    # Get user playlist data, render page
    pm = PlaylistManager(session['user_id'])
    pm.update()
    return render_template('playlists.html', dwu=pm.dwuId, dwh=pm.dwhId, dw=pm.dwId)


if __name__ == '__main__':
    server.run()
