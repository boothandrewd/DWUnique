""" app/updatePlaylists.py
Script issued by Heroku Scheduler to update DwUniques.
"""
import os
from datetime import date

from pymongo import MongoClient
from twilio.rest import TwilioRestClient

from app.RecordManager import RecordManager

# API objects
client = TwilioRestClient(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'])
TWILIO_NUMBER = os.environ['TWILIO_NUMBER']


# Helper function
def send_sms(mobile_number, body):
    """ Text sending function """
    client.messages.create(to=mobile_number, from_=TWILIO_NUMBER, body=body)


# Only update on Mondays
if date.today().weekday() == 0:
    # It's a Monday, so update the playlists

    # Get list of playlist ids
    archives = MongoClient(os.environ['MONGODB_URI']).get_default_database().archives
    playlist_id_dicts = archives.find({'playlist_id': {'$exists': True}}, {
        '_id': 0,
        'playlist_id': 1
    })
    playlist_ids = [pid['playlist_id'] for pid in playlist_id_dicts]

    # Loop through playlist ids and update
    for playlist_id in playlist_ids:
        rc = RecordManager(playlist_id)
        updated, filtered = rc.update()
        if updated and rc.mobileNumber is not None:
            message = 'Your DWUnique has been updated!'
            message += '\nAnd there were some songs filtered!' if filtered else ''
            message += '\nCheck it out at %s/playlist/%s' % (os.environ['APP_URL'], playlist_id)
            send_sms(rc.mobileNumber, message)
