""" app/__init__.py
"""
from flask import Flask, redirect, render_template, request
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials as spCreds

from app.ArchiveManager import ArchiveManager
from app.utils import parse_playlist_resource

# Set up spotipy
spotify = spotipy.Spotify(client_credentials_manager=spCreds())

# Set up flask
server = Flask(__name__)
server.config.from_pyfile('config.py')

@server.route('/', methods=['GET', 'POST'])
def start():
    error = {}
    # On POST use input
    if request.method == 'POST':
        # Get resource from form
        playlist_id = parse_playlist_resource(request.form['pl_resource'])
        mobile_number = request.form['mobile_number'] or None

        # Initialize archive manager
        try:
            am = ArchiveManager(playlist_id, mobile_number)
        except (ValueError, spotipy.client.SpotifyException):
            error['resource'] = 'Please enter a valid URL, URI, or ID'

        # Redirect user to playlist page
        if len(error) == 0:
            am.update()
            return redirect('/playlist/' + playlist_id)

    # On GET render template
    return render_template('start.html', error=error)


@server.route('/playlist/<playlist_id>')
def playlist_page(playlist_id):
    am = ArchiveManager(playlist_id)
    return render_template('playlist.html', playlist=am.getCurrentPlaylist())
