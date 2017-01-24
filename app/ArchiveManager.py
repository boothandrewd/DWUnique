# TODO Refactor pretty much this entire class. Probably should implement some memoization with db checking
""" app/ArchiveManager.py
Database interface.
"""
import os

from pymongo import MongoClient
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials as spCreds

from app.utils import is_hash, clean_mobile_number, today_as_string, date_to_week as d2w

archives = MongoClient(os.environ['MONGODB_URI']).get_default_database().archives
spotify = spotipy.Spotify(client_credentials_manager=spCreds())


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
        if target_archive is None:
            archives.insert_one({
                'playlist_id': self.playlistId,
                'mobile_number': mobile_number and clean_mobile_number(mobile_number),
                'playlists': {},
                'playlist_date': ''
            })
            self.update()

    def update(self):
        """ Updates database with new stuff """
        self.addToDwUniques(self.getSpotifyUniques())

    # Mobile Number Methods

    def setMobileNumber(self, mobile_number):
        """ A setter for a user's mobile number. """
        archives.update_one(self.playlist_filter, {
            '$set': {'mobile_number': clean_mobile_number(mobile_number)}
        })

    def getMobileNumber(self):
        """ A getter for a user's mobile number. """
        return archives.find_one(self.playlist_filter, {
            '_id': 0,
            'mobile_number': 1
        })['mobile_number']

    # Database DWUnique Methods

    def addToDwUniques(self, new_tracks):
        # FIXME Always overwrites date, duh
        today_string = today_as_string()
        archives.update_one(self.playlist_filter, {
            '$set': {
                'playlist_date': today_string,
                'playlists.' + today_string: new_tracks
            },
        })

    def getDwUniques(self):
        """ Gets list of dated DwUniques. """
        return archives.find_one(self.playlist_filter, {
            '_id': 0,
            'playlists': 1
        })['playlists'] or {}

    def getDwUniqueDate(self):
        return archives.find_one(self.playlist_filter, {
            '_id': 0,
            'playlist_date': 1
        })['playlist_date']

    def getDwUnique(self):
        """ Gets a list of track_ids referring to the current DwUnique. """
        try:
            return self.getDwUniques()[self.getDwUniqueDate()] or []
        except KeyError:
            return []

    def getAllTracks(self):
        """ Gets a list of all previous tracks by track_id. """
        return [val for val in self.getDwUniques().values() for val in val]

    # Spotify DW Methods

    def getSpotifyDw(self):
        """ Returns a list of track_ids from the DW current on Spotify """
        sdw = spotify.user_playlist('spotify', self.playlistId)
        return [item['track']['id'] for item in sdw['tracks']['items']]

    def getSpotifyUniques(self):
        """ Returns a list of track_ids that are unique from previous tracks """
        return list(set(self.getSpotifyDw()) & set(self.getAllTracks()))

    def songsWereFiltered(self):
        """ Returns True if songs were filtered """
        return bool(set(self.getSpotifyDw() ^ set(self.getAllTracks())))

    # Other Methods

    def updatedThisWeek(self):
        """ Returns True if the playlist was already updated this week """
        return d2w(today_as_string()) == d2w(self.getDwUniqueDate())

    def playlistIsNew(self):
        """ Returns True if there are new songs in the unique playlist """
        return self.getSpotifyUniques() != self.getDwUnique()
