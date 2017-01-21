""" app/ArchiveManager.py
Database interface.
"""
import os
from datetime import date, datetime

from pymongo import MongoClient
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials as spCreds

from app.utils import is_hash, clean_mobile_number

archives = MongoClient(os.environ['MONGODB_URI']).DWUnique.archives
spotify = spotipy.Spotify(client_credentials_manager=spCreds())

TIME_FORMAT = '%A_%d_%b_%Y'

def date_to_week(date_string):
    """ Date string to week function. """
    return datetime.strptime(date_string, TIME_FORMAT).isocalendar()[1]


class ArchiveManager:
    def __init__(self, playlist_id, mobile_number=None):
        """ Initializes object and creates object in database if necessary. """
        try:
            if not is_hash(playlist_id):
                raise ValueError
            spotify.user_playlist('spotify', playlist_id)
        except Exception as e:
            raise e

        self.playlistId = playlist_id
        self.playlist_filter = {'playlist_id': self.playlistId}
        target_archive = archives.find_one(self.playlist_filter)
        if target_archive == None:
            archives.insert_one({
                'playlist_id': self.playlistId,
                'mobile_number': mobile_number and clean_mobile_number(mobile_number),
                'playlists': {},
                'playlist_date': ''
            })

    def setNumber(self, mobile_number):
        """ A setter for a user's mobile number. """
        archives.update_one(self.playlist_filter, {
            '$set': {'mobile_number': clean_mobile_number(mobile_number)}
        })

    def getNumber(self):
        """ A getter for a user's mobile number. """
        return archives.find_one(self.playlist_filter, {
            '_id': 0,
            'mobile_number': 1
        })['mobile_number']

    def getCurrentPlaylist(self):
        """ Gets a list of track_ids referring to the current DWUnique. """
        try:
            return self.getPlaylists()[self.getCurrentPlaylistDate()] or []
        except:
            return []

    def getCurrentPlaylistDate(self):
        return archives.find_one(self.playlist_filter, {
            '_id': 0,
            'playlist_date': 1
        })['playlist_date']

    def getPlaylists(self):
        """ Gets list of dated DWUniques. """
        return archives.find_one(self.playlist_filter, {
            '_id': 0,
            'playlists': 1
        })['playlists'] or {}

    def getHistory(self):
        """ Gets a list of all previous tracks by track_id. """
        return [val for val in self.getPlaylists().values() for val in val]

    def update(self):
        """ Determines the current new playlist and updates database. """
        # Get Spotify's DW
        sdw = spotify.user_playlist('spotify', self.playlistId)
        sdw_tracks = [item['track']['id'] for item in sdw['tracks']['items']]

        # Determine which tracks are new
        new_tracks = list(set(sdw_tracks) - set(self.getHistory()))

        # If there are new tracks, update database
        if new_tracks != self.getCurrentPlaylist():
            today_string = date.today().strftime(TIME_FORMAT)
            res = archives.update_one(self.playlist_filter, {
                '$set': {
                    'playlist_date': today_string,
                    'playlists.' + today_string: new_tracks
                },
            })
            return True

        return False
