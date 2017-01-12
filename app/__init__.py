""" app/__init__.py
"""
import os

from flask import Flask, redirect, render_template, request
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials as spCreds

from app.playlistUtils import updateList

# Set up spotipy
ccm = spCreds(os.environ['CLIENT_ID'], os.environ['CLIENT_SECRET'])
sp = spotipy.Spotify(client_credentials_manager=ccm)

# Set up flask
app = Flask(__name__)
app.config.from_pyfile('config.py')

@app.route('/')
def index():
    return redirect('/start')

@app.route('/start', methods=['GET', 'POST'])
def start():
    error = ''
    # On POST use input
    if request.method == 'POST':
        # Get resource from form
        dw_resource = request.form['dw_resource']
        delimiter = '/'
        if dw_resource.startswith('spotify'):
            delimiter = ':'

        # Get playlist id from form input
        playlist_id = dw_resource.split(delimiter)[-1]

        # Attempt to get reference to playlist
        try:
            dw = sp.user_playlist('spotify', playlist_id)
        except spotipy.client.SpotifyException:
            error = 'Please enter a valid URL, URI, or ID'

        # Redirect user to playlist page
        if not error:
            updateList(playlist_id)
            return redirect('/playlist/{}'.format(playlist_id))

    # On GET render template
    return render_template('start.html', error=error)

@app.route('/playlist/<playlist_id>')
def playlist_page(playlist_id):
    return playlist_id
