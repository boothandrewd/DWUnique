""" app/utils.py
"""
import os
from datetime import date

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials as spCreds
from pymongo import MongoClient

TIME_FORMAT = '%a %d %b %Y'

# Set up mongo
plArchives = MongoClient(os.environ['MONGODB_URI']).pl_tracker.plArchives

# Set up spotipy
ccm = spCreds(os.environ['CLIENT_ID'], os.environ['CLIENT_SECRET'])
spotify = spotipy.Spotify(client_credentials_manager=ccm)


def update_mobile_number(playlist_id, mobile_number):
    plArchives.update_one({'playlist_id': playlist_id}, {
        '$set': {
            'mobile_number': mobile_number
        }
    }, upsert=True)


def update_update_day(playlist_id, day_index):
    plArchives.update_one({'playlist_id': playlist_id}, {
        '$set': {
            'update_day': day_index
        }
    }, upsert=True)


def update_plArchive(playlist_id):
    # Get database info
    db_track_list = plArchives.find_one({'playlist_id': playlist_id}, ['track_list']) or []
    db_dwu_track_ids = plArchives.find_one({'playlist_id': playlist_id}, ['dwu']) or []

    # Get new track ids from playlist object
    pl = spotify.user_playlist('spotify', playlist_id)
    new_track_ids = set([item['track']['id'] for item in pl['tracks']['items']])

    # Determine new DWU
    old_track_ids = set([track[0] for track in db_track_list])
    dwu_track_ids = list(new_track_ids - old_track_ids)
    # If new DWU is different from db, overwrite db
    if dwu_track_ids != db_dwu_track_ids:
        dwu_update = {'$set': {'dwu': dwu_track_ids}}
    else:
        dwu_update = {}

    # Create track list
    today_string = date.today().strftime(TIME_FORMAT)
    track_list = []
    for dwu_track_id in dwu_track_ids:
        track_list.append((dwu_track_id, today_string))
    track_list_update = {'$addToSet': {'track_list': {'$each': track_list}}}

    # Update database
    plArchives.update_one({'playlist_id': playlist_id}, {**track_list_update, **dwu_update}, upsert=True)
