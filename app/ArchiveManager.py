""" app/ArchiveManager.py
"""
import os
from datetime import date

from pymongo import MongoClient
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials as spCreds

from app.utils import is_hash, clean_mobile_number

TIME_FORMAT = '%A_%d_%b_%Y'

archives = MongoClient(os.environ['MONGODB_URI']).DWUnique.archives
spotify = spotipy.Spotify(client_credentials_manager=spCreds())


class ArchiveManager:
    def __init__(self, playlist_id, mobile_number=None):
        try:
            if not is_hash(playlist_id):
                raise ValueError
            spotify.user_playlist('spotify', playlist_id)
        except Exception as e:
            raise e

        self.playlistId = playlist_id
        self.playlist_filter = {'playlist_id': self.playlistId}
        target_archive = archives.find_one(self.playlist_filter)
        if not target_archive:
            archives.insert_one({
                'playlist_id': self.playlistId,
                'mobile_number': mobile_number and clean_mobile_number(mobile_number),
                'playlists': [],
                'playlist': []
            })

    def setNumber(self, mobile_number):
        archives.update_one(self.playlist_filter, {
            '$set': {'mobile_number': clean_mobile_number(mobile_number)}
        })

    def getNumber(self):
        return archives.find_one(self.playlist_filter, {
            '_id': 0,
            'mobile_number': 1
        })['mobile_number'] or None

    def getCurrentPlaylist(self):
        return archives.find_one(self.playlist_filter, {
            '_id': 0,
            'playlist': 1
        })['playlist'] or []

    def getPlaylists(self):
        return archives.find_one(self.playlist_filter, {
            '_id': 0,
            'playlists': 1
        })['playlists'] or []

    def getHistory(self):
        return [i for t in self.getPlaylists() for i in t[1]]

    def update(self):
        playlist_updated = False
        # Get Spotify's DW
        sdw = spotify.user_playlist('spotify', self.playlistId)
        sdw_tracks = [item['track']['id'] for item in sdw['tracks']['items']]

        # Determine which tracks are new
        new_tracks = list(set(sdw_tracks) - set(self.getHistory()))

        # If there are new tracks, update database
        if new_tracks != self.getCurrentPlaylist():
            today_string = date.today().strftime(TIME_FORMAT)
            archives.update_one(self.playlist_filter, {
                '$set': {'playlist': new_tracks},
                '$push': {'playlists': (today_string, new_tracks)}
            })
            playlist_updated = True
        return playlist_updated
