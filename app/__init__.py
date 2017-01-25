""" app/__init__.py
"""
from flask import Flask, redirect, render_template, request
import spotipy

from app.RecordManager import RecordManager


# Helper function
def parse_playlist_resource(resource):
    return resource.split(':' if resource.startswith('spotify') else '/')[-1]


# Set up flask
server = Flask(__name__)
server.config.from_pyfile('config.py')


# Routes
@server.route('/', methods=['GET', 'POST'])
def start():
    error = {}
    # On POST use input
    if request.method == 'POST':
        # Get resource from form
        playlist_id = parse_playlist_resource(request.form['pl_resource'])
        mobile_number = request.form['mobile_number'] or None

        # Initialize record
        try:
            RecordManager(playlist_id, mobile_number)
        except spotipy.client.SpotifyException:
            error['resource'] = 'Please enter a valid URL, URI, or ID'

        # Redirect user to playlist page
        if len(error) == 0:
            return redirect('/playlist/' + playlist_id)

    # On GET render template
    return render_template('start.html', error=error)


@server.route('/playlist/<playlist_id>')
def playlist_page(playlist_id):
    return render_template('dashboard.html', playlist=RecordManager(playlist_id).getDwUniqueSongData())


@server.route('/playlist/<playlist_id>/number_change', methods=['POST'])
def number_change(playlist_id):
    RecordManager(playlist_id).setMobileNumber(request.form['mobile_number'])


if __name__ == '__main__':
    server.run()
