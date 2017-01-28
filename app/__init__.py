""" app/__init__.py
"""
import json
import os
from urllib.parse import urlencode

import requests
from flask import Flask, redirect, render_template, request, session
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from pymongo import MongoClient

from app.RecordManager import RecordManager
from app.PlaylistManager import PlaylistManager

# Set up flask
server = Flask(__name__)
server.config.from_pyfile('config.py')
users = MongoClient(os.environ['MONGODB_URI']).get_default_database().users


# Helper function
def parse_playlist_resource(resource):
    return resource.split(':' if resource.startswith('spotify') else '/')[-1]

# Auth constants
USER_AUTH_PARAMS = {
    'response_type': 'code',
    'redirect_uri': os.environ['SPOTIPY_REDIRECT_URI'],
    'scope': 'user-read-email',
    'state': 'user-auth',
    'client_id': os.environ['SPOTIPY_CLIENT_ID']
}


# Routes
@server.route('/')
def index():
    if 'user_id' in session:
        return redirect('/playlists')
    else:
        return redirect('/signin')


@server.route('/signin', methods=['GET', 'POST'])
def signin():
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
        'redirect_uri': os.environ['SPOTIPY_REDIRECT_URI'],
        'client_id': os.environ['SPOTIPY_CLIENT_ID'],
        'client_secret': os.environ['SPOTIPY_CLIENT_SECRET']
    })
    access_data = json.loads(access_response.text)
    access_token = access_data['access_token']
    refresh_token = access_data['refresh_token']
    auth_spotify = spotipy.Spotify(access_token, client_credentials_manager=SpotifyClientCredentials())

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
            'mobile_number': '',
            'refresh_token': refresh_token,
            'dw_id': '',
            'dwu_id': '',
            'dwh_id': ''
        })
    session['user_id'] = user_id

    return redirect('/playlists')


@server.route('/connect', methods=['GET', 'POST'])
def connect():
    if 'user_id' not in session:
        return redirect('/signin')

    if request.method == 'POST':
        # Get submitted playlist id
        playlist_id = parse_playlist_resource(request.form['pl-resource'])

        # Verify it actually exists on Spotify servers
        try:
            spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials()).user_playlist('spotify', playlist_id)
        except spotipy.client.SpotifyException:
            return render_template('connect.html', error='Please enter a valid URL, URI, or ID')

        # Update database with playlist id
        users.update_one({'user_id': session['user_id']}, {
            '$set': {'dw_id': playlist_id}
        })

        # Redirect user to their playlists
        return redirect('/playlists')

    return render_template('connect.html', error='')


@server.route('/playlists')
def playlists():
    if 'user_id' not in session:
        return redirect('/')

    user_record = users.find_one({'user_id': session['user_id']})
    if user_record['dw_id'] == '':
        return redirect('/connect')

    pm = PlaylistManager(session['user_id'])
    print(pm)
    return render_template('playlists.html', dwu='')



# # Routes
# @server.route('/', methods=['GET', 'POST'])
# def start():
#     error = {}
#     # On POST use input
#     if request.method == 'POST':
#         # Get resource from form
#         playlist_id = parse_playlist_resource(request.form['pl_resource'])
#         mobile_number = request.form['mobile_number'] or None
#
#         # Initialize record
#         try:
#             RecordManager(playlist_id, mobile_number)
#         except spotipy.client.SpotifyException:
#             error['resource'] = 'Please enter a valid URL, URI, or ID'
#
#         # Redirect user to playlist page
#         if len(error) == 0:
#             return redirect('/playlist/' + playlist_id)
#
#     # On GET render template
#     return render_template('connect.html', error=error)
#
#
# @server.route('/playlist/<playlist_id>')
# def playlist_page(playlist_id):
#     return render_template('dashboard.html', playlist=RecordManager(playlist_id).getDwUniqueSongData())
#
#
# @server.route('/playlist/<playlist_id>/number_change', methods=['POST'])
# def number_change(playlist_id):
#     RecordManager(playlist_id).setMobileNumber(request.form['mobile_number'])
#
#
# # Spotify auth code flow testing zone
# import os
# import urllib
#
# # Spotify URLs
# SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
# SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
# SPOTIFY_API_BASE_URL = "https://api.spotify.com"
# API_VERSION = "v1"
# SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)
#
# # Server-side parameters
# CLIENT_SIDE_URL = "http://localhost"
# PORT = 5000
# REDIRECT_URI = "{}:{}/callback".format(CLIENT_SIDE_URL, PORT)
# SCOPE = "playlist-modify-public playlist-modify-private"
# STATE = "sekret"
# SHOW_DIALOG_bool = True
# SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()
#
# auth_query_parameters = {
#     'response_type': 'code',
#     'redirect_uri': REDIRECT_URI,
#     'scope': SCOPE,
#     'state': STATE,
#     'client_id': os.environ['SPOTIPY_CLIENT_ID']
# }
#
# @server.route('/auth')
# def auth():
#     url_args = '&'.join('{}={}'.format(key, quote(val)) for key, val in USER_AUTH_PARAMS.items())
#     auth_url = '{}/?{}'.format(SPOTIFY_AUTH_URL, url_args)
#     print(auth_url)
#     return redirect(auth_url)
#
#
# @server.route('/callback')
# def callback():
#     # Auth Step 4: Requests refresh and access tokens
#     auth_token = request.args['code']
#     code_payload = {
#         "grant_type": "authorization_code",
#         "code": str(auth_token),
#         "redirect_uri": REDIRECT_URI,
#         'client_id': os.environ['SPOTIPY_CLIENT_ID'],
#         'client_secret': os.environ['SPOTIPY_CLIENT_SECRET']
#     }
#     # base64encoded = base64.b64encode(
#     #     "{}:{}".format(os.environ['SPOTIPY_CLIENT_ID'], os.environ['SPOTIPY_CLIENT_SECRET']).encode('ascii')
#     # )
#     # base64encoded = b64(os.environ['SPOTIPY_CLIENT_ID'].encode('ascii')) + b':' + b64(os.environ['SPOTIPY_CLIENT_SECRET'].encode('ascii'))
#     # headers = {"Authorization": "Basic {}".format(base64encoded)}
#     post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload)
#     # post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, headers=headers)
#
#     # Auth Step 5: Tokens are Returned to Application
#     response_data = json.loads(post_request.text)
#     access_token = response_data["access_token"]
#     refresh_token = response_data["refresh_token"]
#     token_type = response_data["token_type"]
#     expires_in = response_data["expires_in"]
#
#     # Auth Step 6: Use the access token to access Spotify API
#     authorization_header = {"Authorization": "Bearer {}".format(access_token)}
#
#     # Get profile data
#     user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
#     profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
#     profile_data = json.loads(profile_response.text)
#
#     # oAuth = SpotifyOAuth(os.environ['SPOTIPY_CLIENT_ID'], os.environ['SPOTIPY_CLIENT_SECRET'], os.environ['SPOTIPY_REDIRECT_URI'])
#     # oAuth.refresh_access_token(refresh_token)
#
#     spotify = spotipy.Spotify(access_token, client_credentials_manager=SpotifyClientCredentials())
#
#     # Get user playlist data
#     playlist_api_endpoint = "{}/playlists".format(profile_data["href"])
#     playlists_response = requests.get(playlist_api_endpoint, headers=authorization_header)
#     playlist_data = json.loads(playlists_response.text)
#
#     return 'lol'
#
#

if __name__ == '__main__':
    server.run()
