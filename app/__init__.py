""" app/__init__.py
"""
import os
import re

from flask import Flask, redirect, render_template, request
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import spotipy.util as util

from app.utils import update_pl_archive, get_latest_unique_playlist

# Constants
CLIENT_ID = os.environ['SPOTIPY_CLIENT_ID']
CLIENT_SECRET = os.environ['SPOTIPY_CLIENT_SECRET']
REDIRECT_URI = os.environ['SPOTIPY_REDIRECT_URI']

# Set up spotipy
# ccm = spCreds()
# sp = spotipy.Spotify(client_credentials_manager=ccm)

# Set up flask
server = Flask(__name__)
server.config.from_pyfile('config.py')

@server.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        token = util.prompt_for_user_token(username, redirect_uri='https://dwunique.herokuapp.com/auth_callback')
        return render_template('playlist.html', playlist=[])
    return render_template('start.html', error='')

@server.route('/auth_callback')
def auth_callback():
    soa = SpotifyOAuth(CLIENT_ID, CLIENT_SECRET, 'https://dwunique.herokuapp.com/auth_callback')
    token = soa.get_access_token(request.args.get('code'))
    return token

# def isHash(candidate):
#     return not re.search(r'\W', candidate)
#
# @server.route('/', methods=['GET', 'POST'])
# def start():
#     if request.method == 'POST':
#         username = request.form['username']
#         token = util.prompt_for_user_token(username)
#         if token:
#             print(token)
#             return render_template('start.html', error='')
#     return render_template('start.html', error='')
#     # error = {}
#     # # On POST use input
#     # if request.method == 'POST':
#     #     # Get resource from form
#     #     pl_resource = request.form['pl_resource']
#     #     delimiter = '/'
#     #     if pl_resource.startswith('spotify'):
#     #         delimiter = ':'
#     #
#     #     # Get playlist id from form input
#     #     playlist_id = pl_resource.split(delimiter)[-1]
#     #     if not isHash(playlist_id):
#     #         error['resource'] = 'Please enter a valid URL, URI, or ID'
#     #
#     #     # Attempt to get reference to playlist
#     #     try:
#     #         pl = sp.user_playlist('spotify', playlist_id)
#     #     except spotipy.client.SpotifyException:
#     #         error['resource'] = 'Please enter a valid URL, URI, or ID'
#     #
#     #     # Redirect user to playlist page
#     #     if len(error) == 0:
#     #         update_pl_archive(playlist_id)
#     #         return redirect('/playlist/' + playlist_id)
#     #
#     # # On GET render template
#     # return render_template('start.html', error=error)
#
#
# @server.route('/auth_callback')
# def auth_callback():
#     print(request)
#     return request
#
# @server.route('/playlist/<playlist_id>')
# def playlist_page(playlist_id):
#     return render_template('playlist.html', playlist=get_latest_unique_playlist(playlist_id))
