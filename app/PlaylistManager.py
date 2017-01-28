""" app/PlaylistManager.py
"""
import os
import json

import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from pymongo import MongoClient

users = MongoClient(os.environ['MONGODB_URI']).get_default_database().users

access_request = requests.post('https://accounts.spotify.com/api/token', data={
    'grant_type': 'refresh_token',
    'refresh_token': os.environ['DWUNIQUE_REFRESH_TOKEN'],
    'client_id': os.environ['SPOTIPY_CLIENT_ID'],
    'client_secret': os.environ['SPOTIPY_CLIENT_SECRET']
})
dw_access_token = json.loads(access_request.content.decode('utf-8'))['access_token']
dwu_spotify = spotipy.Spotify(dw_access_token, client_credentials_manager=SpotifyClientCredentials())


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
                dwu = dwu_spotify.user_playlist_create('dwunique', "DWUnique")
                dwh = dwu_spotify.user_playlist_create('dwunique', "DW History")

            users.update_one({'user_id': self.userId}, {
                '$set': {
                    'dwu_id': dwu['id'],
                    'dwh_id': dwh['id']
                }
            })


    def update(self):
        pass


    def
