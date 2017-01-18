""" app/utils.py
"""
import os
import re
from datetime import date, datetime

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials as spCreds
from pymongo import MongoClient

TIME_FORMAT = '%A_%d_%b_%Y'

# Set up mongo
pl_archives = MongoClient(os.environ['MONGODB_URI']).pl_tracker.pl_archives

# Set up spotipy
ccm = spCreds(os.environ['CLIENT_ID'], os.environ['CLIENT_SECRET'])
spotify = spotipy.Spotify(client_credentials_manager=ccm)


def update_mobile_number(playlist_id, mobile_number):
    re.sub(r'\D', '', mobile_number)
    pl_archives.update_one({'playlist_id': playlist_id}, {
        '$set': {'mobile_number': mobile_number}
    }, upsert=True)


def update_scan_day(playlist_id, day_index):
    pl_archives.update_one({'playlist_id': playlist_id}, {
        '$set': {'scan_day': day_index}
    }, upsert=True)


def get_history_set(playlist_id):
    unique_playlists = pl_archives.find_one({'playlist_id': playlist_id}, {
        'unique_playlists': 1,
        '_id': 0
    })['unique_playlists'] or {}
    return set([ti for up in unique_playlists.values() for ti in up])


def get_latest_unique_playlist(playlist_id):
    unique_playlists = pl_archives.find_one({'playlist_id': playlist_id}, {
        'unique_playlists': 1,
        '_id': 0
    })['unique_playlists'] or {}
    latest_date = sorted(unique_playlists.keys(), key=lambda x: datetime.strptime(x, TIME_FORMAT), reverse=True)[0]
    print(latest_date)
    return unique_playlists[latest_date]


def update_pl_archive(playlist_id):
    # Get Spotify playlist's current tracks
    pl = spotify.user_playlist('spotify', playlist_id)
    current_spotify_tracks = set([item['track']['id'] for item in pl['tracks']['items']])

    # Determine which tracks are new
    new_tracks = list(current_spotify_tracks - get_history_set(playlist_id))

    # Update database
    today_string = date.today().strftime(TIME_FORMAT)
    pl_archives.update_one({'playlist_id': playlist_id}, {
        '$set': {'unique_playlists.' + today_string: new_tracks}
    }, upsert=True)
