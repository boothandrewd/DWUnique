""" updateUtils.py
"""
import os
import datetime

import pymongo
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials as spCreds

# Set up mongo
from pymongo import MongoClient
client = MongoClient(os.environ['MONGODB_URI'])

# Set up spotipy
ccm = spCreds(os.environ['CLIENT_ID'], os.environ['CLIENT_SECRET'])
sp = spotipy.Spotify(client_credentials_manager=ccm)

def updateList(playlist_id):
    users = client.dw_tracker.users
    user = users.find_one({'playlist_id': playlist_id})
    if not user:
        user = {
            'playlist_id': playlist_id,
            'history': [],
            'track_set': []
        }
        users.insert_one(user)

    try:
        dw = sp.user_playlist('spotify', playlist_id)
    except spotipy.client.SpotifyException:
        pass


def updateLists():
    users = client.dw_tracker.users
    for user in users.find():
        print(user)
