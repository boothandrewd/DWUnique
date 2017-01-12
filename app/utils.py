""" app/utils.py
"""
import os
import re
from datetime import date

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
    unique_playlists = pl_archives.find_one({'playlist_id': playlist_id}, ['unique_playlists']) or {}
    return set([ti for up in unique_playlists.values() for ti in up])


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
    })


# def update_pl_archive(playlist_id):
#     # Get database info
#     db_track_list = pl_archives.find_one({'playlist_id': playlist_id}, ['track_list']) or []
#     db_dwu_track_ids = pl_archives.find_one({'playlist_id': playlist_id}, ['dwu']) or []
#
#     # Get new track ids from playlist object
#     pl = spotify.user_playlist('spotify', playlist_id)
#     new_track_ids = set([item['track']['id'] for item in pl['tracks']['items']])
#
#     # Determine new DWU
#     old_track_ids = set([track[0] for track in db_track_list])
#     dwu_track_ids = list(new_track_ids - old_track_ids)
#     # If new DWU is different from db, overwrite db
#     if dwu_track_ids != db_dwu_track_ids:
#         dwu_update = {'$set': {'dwu': dwu_track_ids}}
#     else:
#         dwu_update = {}
#
#     # Create track list
#     today_string = date.today().strftime(TIME_FORMAT)
#     track_list = []
#     for dwu_track_id in dwu_track_ids:
#         track_list.append((dwu_track_id, today_string))
#     track_list_update = {'$addToSet': {'track_list': {'$each': track_list}}}
#
#     # Update database
#     pl_archives.update_one({'playlist_id': playlist_id}, {**track_list_update, **dwu_update}, upsert=True)
