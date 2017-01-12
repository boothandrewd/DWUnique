""" app/PlArchiveManager.py
"""
import os

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials as spCreds
from pymongo import MongoClient

# Set up mongo
plArchives = MongoClient(os.environ['MONGODB_URI']).dw_tracker.plArchives

# Set up spotipy
ccm = spCreds(os.environ['CLIENT_ID'], os.environ['CLIENT_SECRET'])
spotify = spotipy.Spotify(client_credentials_manager=ccm)

# spotify:user:spotify:playlist:37i9dQZEVXcPsqrzUr4kra
playlist = spotify.user_playlist('spotify', '37i9dQZEVXcPsqrzUr4kra')
# print(dw['tracks']['items'][0]['track']['id'])
playlist_track_ids = [item['track']['id'] for item in playlist['tracks']['items']]
# print(playlist_track_ids)

class PlArchiveManager:
    def __init__(self, playlist_id, phone_number=None):
        # Check in with database
        plArchive = plArchives.find_one({'playlist_id': playlist_id})
        if plArchive == None:
            plArchive = {
                'playlist_id': playlist_id,
                'phone_number': phone_number,
                'track_ids_by_time': [],
                'track_id_set': []
                'weeks_playlist': []
            }
            plArchives.insert_one(plArchive)

        # Initialize locals
        self.playlistId = playlist_id
        self.phoneNumber = plArchive['phone_number']
        self.trackIdsByTime = plArchive['track_ids_by_time']
        self.trackSet = set(plArchive['track_id_set'])
        self.weeksPlaylist = 

    def getCurrentWeeksPl(self):
        # Get current state of playlist from Spotify
        pl = spotify.user_playlist('spotify', self.playlistId)
        pl_track_ids = set([item['track']['id'] for item in pl['tracks']['items']])

        # Return list of unique tracks ids
        return list(pl_track_ids - self.track_set)

    def updatePlArchive(self):
        # Get unique new tracks
        unique_tracks = self.getCurrentWeeksPl()

        # Add tracks to track set
        self.track
