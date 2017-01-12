""" app/__init__.py
"""
import os
import re

from flask import Flask, redirect, render_template, request
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials as spCreds

from app.utils import update_pl_archive

# Set up spotipy
ccm = spCreds(os.environ['CLIENT_ID'], os.environ['CLIENT_SECRET'])
sp = spotipy.Spotify(client_credentials_manager=ccm)

# Set up flask
server = Flask(__name__)
server.config.from_pyfile('config.py')

def isHash(candidate):
    return not re.search(r'\W', candidate)

@server.route('/')
def index():
    return redirect('/start')

@server.route('/start', methods=['GET', 'POST'])
def start():
    error = ''
    # On POST use input
    if request.method == 'POST':
        # Get resource from form
        pl_resource = request.form['pl_resource']
        delimiter = '/'
        if pl_resource.startswith('spotify'):
            delimiter = ':'

        # Get playlist id from form input
        playlist_id = pl_resource.split(delimiter)[-1]
        if not isHash(playlist_id):
            error = 'Please enter a valid URL, URI, or ID'

        # Attempt to get reference to playlist
        try:
            pl = sp.user_playlist('spotify', playlist_id)
        except spotipy.client.SpotifyException:
            error = 'Please enter a valid URL, URI, or ID'

        # Redirect user to playlist page
        if not error:
            updateList(playlist_id)
            return redirect('/playlist/' + playlist_id)

    # On GET render template
    return render_template('start.html', error=error)

@server.route('/playlist/<playlist_id>')
def playlist_page(playlist_id):
    return playlist_id
