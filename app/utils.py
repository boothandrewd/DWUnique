""" app/utils.py
"""
import os
import re
from datetime import datetime, date

from twilio.rest import TwilioRestClient
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials as spCreds

TIME_FORMAT = '%A_%d_%b_%Y'

client = TwilioRestClient(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'])
TWILIO_NUMBER = os.environ['TWILIO_NUMBER']

spotify = spotipy.Spotify(client_credentials_manager=spCreds())


def parse_playlist_resource(resource):
    """ Playlist parsing resource function """
    delimiter = '/'
    if resource.startswith('spotify'):
        delimiter = ':'
    return resource.split(delimiter)[-1]


def clean_mobile_number(mobile_number):
    """ Mobile number checking function """
    return re.sub(r'\D', '', mobile_number)


def is_hash(candidate):
    """ Hash checking function """
    return not re.search(r'\W', candidate)


def send_sms(mobile_number, message):
    """ Text sending function """
    client.messages.create(to=mobile_number, from_=TWILIO_NUMBER, body=message)


def date_to_week(date_string):
    """ Date string to week function. """
    return datetime.strptime(date_string, TIME_FORMAT).isocalendar()[1]


def today_as_string():
    """ Returns the current day in the standard format """
    return date.today().strftime(TIME_FORMAT)


def get_track_info(track_list):
    for track_id in track_list:
        track = spotify.track(track_id)
        print(track['name'])
        # print(track['artists'][0]['name'])
