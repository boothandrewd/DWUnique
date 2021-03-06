""" app/PlaylistManager.py
"""
import json
from datetime import datetime

import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from pymongo import MongoClient

from app import MONGODB_URI, DWUNIQUE_REFRESH_TOKEN, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

# Get database connection
users = MongoClient(MONGODB_URI).get_default_database().users

# Get access to DWUnique Spotify account
access_request = requests.post('https://accounts.spotify.com/api/token', data={
    'grant_type': 'refresh_token',
    'refresh_token': DWUNIQUE_REFRESH_TOKEN,
    'client_id': SPOTIFY_CLIENT_ID,
    'client_secret': SPOTIFY_CLIENT_SECRET
})
dw_access_token = json.loads(access_request.content.decode('utf-8'))['access_token']
dwu_spotify = spotipy.Spotify(
    auth=dw_access_token,
    client_credentials_manager=SpotifyClientCredentials(
        SPOTIFY_CLIENT_ID,
        SPOTIFY_CLIENT_SECRET
    )
)


class PlaylistManager:
    def __init__(self, user_id):
        self.userId = user_id
        # Get user data
        user_record = users.find_one({'user_id': self.userId})

        # If no DWU exists yet, create it
        if user_record['dwu_id'] == '':
            display_name = user_record['user_display_name']
            if display_name is not None:
                dwu = dwu_spotify.user_playlist_create('dwunique', f"{display_name}'s DWUnique")
                dwh = dwu_spotify.user_playlist_create('dwunique', f"{display_name}'s DW History")
            else:
                dwu = dwu_spotify.user_playlist_create('dwunique', 'DWUnique')
                dwh = dwu_spotify.user_playlist_create('dwunique', 'DW History')

            # Add to database
            users.update_one({'user_id': self.userId}, {
                '$set': {
                    'dwu_id': dwu['id'],
                    'dwh_id': dwh['id']
                }
            })
            user_record = users.find_one({'user_id': self.userId})

            # Have user follow playlist
            access_request = requests.post('https://accounts.spotify.com/api/token', data={
                'grant_type': 'refresh_token',
                'refresh_token': user_record['refresh_token'],
                'client_id': SPOTIFY_CLIENT_ID,
                'client_secret': SPOTIFY_CLIENT_SECRET
            })
            access_token = json.loads(access_request.content.decode('utf-8'))['access_token']
            auth_spotify = spotipy.Spotify(
                auth=access_token,
                client_credentials_manager=SpotifyClientCredentials(
                    SPOTIFY_CLIENT_ID,
                    SPOTIFY_CLIENT_SECRET
                )
            )
            auth_spotify.user_playlist_follow_playlist('dwunique', user_record['dwu_id'])

        # Populate members
        self.dwId = user_record['dw_id']
        self.dwuId = user_record['dwu_id']
        self.dwhId = user_record['dwh_id']
        self._mobileNumber = user_record['mobile_number']
        self._mobileUpdateSetting = user_record['mobile_update_setting']

    def update(self):
        # Get user data
        user_record = users.find_one({'user_id': self.userId})

        # Get current date data
        today = datetime.today()
        this_week = today.isocalendar()[1]
        today_date = today.strftime('%Y-%m-%d')

        # Figure out if it's okay to update
        last_update_date = user_record['last_update']
        if last_update_date == '':
            update_needed = True
        else:
            # Get last update week
            last_update_week = datetime.strptime(last_update_date, '%Y-%m-%d').isocalendar()[1]
            update_needed = last_update_week != this_week

        if update_needed:
            # Get new DW
            dw = dwu_spotify.user_playlist('spotify', user_record['dw_id'])
            dw_track_ids = [item['track']['id'] for item in dw['tracks']['items']]

            # Get DW History
            dwh = dwu_spotify.user_playlist('dwunique', user_record['dwu_id'])
            dwh_track_ids = [item['track']['id'] for item in dwh['tracks']['items']]

            # Find unique tracks
            dwu_track_ids = list(set(dw_track_ids) - set(dwh_track_ids))

            # Remove all songs from DWU
            dwu_spotify.user_playlist_remove_all_occurrences_of_tracks(
                'dwunique',
                user_record['dwu_id'],
                dwh_track_ids
            )

            # Add new tracks to DWU
            dwu_spotify.user_playlist_add_tracks(
                'dwunique',
                user_record['dwu_id'],
                dwu_track_ids
            )

            # Add new tracks to DW History
            dwu_spotify.user_playlist_add_tracks(
                'dwunique',
                user_record['dwh_id'],
                dwu_track_ids
            )

            # Update update date in database
            users.update_one({'user_id': self.userId}, {
                '$set': {'last_update': today_date}
            })

            return True
        return False

    def setMobileNumber(self, mobile_number):
        self._mobileNumber = mobile_number
        users.update_one({'user_id': self.userId}, {
            '$set': {'mobile_number': self._mobileNumber}
        })

    def getMobileNumber(self):
        return self._mobileNumber

    def setmobileUpdateSetting(self, setting):
        self._mobileUpdateSetting = setting
        users.update_one({'user_id': self.userId}, {
            '$set': {'mobile_update_setting': self._mobileUpdateSetting}
        })

    def getmobileUpdateSetting(self):
        return self._mobileUpdateSetting
