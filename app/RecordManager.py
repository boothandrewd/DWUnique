""" app/RecordManager.py
"""
import os
import re

from datetime import datetime, date

from pymongo import MongoClient
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Constants
TIME_FORMAT = '%Y-%m-%d'

# API objects
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
dwunique_db = MongoClient(os.environ['MONGODB_URI']).get_default_database()
archives = dwunique_db.archives
songs = dwunique_db.songs


# Helper functions
def sanitize_number(number):
    return re.sub(r'\D', '', number) if number else None      # TODO Sanitize forms on the way in and remove this step


def parse_spotify_playlist(playlist_id):
    # Get Spotify data and initialize lists
    playlist_object = spotify.user_playlist('spotify', playlist_id)
    playlist_data = []
    track_ids = []

    # Loop through tracks and populate lists
    for song in playlist_object['tracks']['items']:
        track = song['track']
        track_id = track['id']

        # Add data to lists
        track_ids.append(track_id)
        playlist_data.append({
            'track_id': track_id,
            'track_name': track['name'],
            'artists': [{'id': artist['id'], 'name': artist['name']} for artist in track['artists']],
            'album_id': track['album']['id'],
            'album_name': track['album']['name']
        })

    # Update song database and return track ids
    songs.insert(playlist_data)
    return track_ids


# Class definition
class RecordManager:
    def __init__(self, safe_playlist_id, mobile_number=None):
        # Raise error if playlist doesnt not exist in db
        try:
            spotify.user_playlist('spotify', safe_playlist_id)
        except Exception as e:
            raise e

        # Set basic locals
        self.playlistId = safe_playlist_id
        self.mobileNumber = sanitize_number(mobile_number)
        self.playlistFilter = {'playlist_id': self.playlistId}

        # Add to database if not already added
        target_archive = archives.find_one(self.playlistFilter)
        if target_archive is None:
            # No record in database, so initialize one

            # Start by rendering current DW data
            today_date = date.today().strftime(TIME_FORMAT)
            dw_track_ids = parse_spotify_playlist(self.playlistId)

            # Add to database
            archives.insert_one({
                'playlist_id': self.playlistId,
                'mobile_number': self.mobileNumber,
                'dwuniques': {today_date: dw_track_ids},
                'last_update_date': today_date
            })

        # Set remaining locals
        target_archive = archives.find_one(self.playlistFilter)
        self.dwUniques = target_archive['dwuniques']
        self.lastUpdateDate = target_archive['last_update_date']

    def update(self):
        last_update_date = datetime.strptime(self.lastUpdateDate, TIME_FORMAT)
        if last_update_date.isocalendar()[1] != date.today().isocalendar()[1]:
            # It's a different week from the current playlist, so update

            # Start by getting Spotify's current DW as track ids (while updating song database)
            spotify_dw_ids = parse_spotify_playlist(self.playlistId)

            # Determine the entire pool of songs from previous playlists
            history_ids = [val for val in self.dwUniques.values() for val in val]

            # Determine the unique songs from spotify, and the songs they have in common
            unique_ids = list(set(spotify_dw_ids) - set(history_ids))
            common_ids = list(set(spotify_dw_ids) & set(history_ids))

            # Update database
            today_date = date.today().strftime(TIME_FORMAT)
            archives.update_one(self.playlistFilter, {
                '$set': {
                    'dwuniques.' + today_date: unique_ids,
                    'last_update_date': today_date
                }
            })

            # Return if updated, filtered
            return True, bool(common_ids)
        return False, False

    def getDwUniqueSongData(self):
        # Return list of song data based on the track ids from the most recent update
        return list(songs.find({
            'track_id': {'$in': self.dwUniques[self.lastUpdateDate]}
        }))

    def getHistoricalSongData(self):
        # Returns dict of song data of all track ids
        historical_song_data = {}
        for date, dwunique in self.dwUniques:
            historical_song_data[date] = list(songs.find({
                'track_id': {'$in': self.dwUniques[date]}
            }))
        return historical_song_data

    def setMobileNumber(self, mobile_number):
        # Sanitize and add locally and to database
        clean_mobile_number = sanitize_number(mobile_number)
        self.mobileNumber = clean_mobile_number
        archives.update_one(self.playlistFilter, {
            '$set': {'mobile_number': clean_mobile_number}
        })
