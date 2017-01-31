""" app/updatePlaylists.py
Script issued by Heroku Scheduler to update DwUniques.
"""
from datetime import date

from pymongo import MongoClient
from twilio.rest import TwilioRestClient

from app import MONGODB_URI, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_NUMBER
from app.PlaylistManager import PlaylistManager

# Twilio object
client = TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


# Only update on Mondays
if date.today().weekday() == 0:
    # Get list of user ids
    users = MongoClient(MONGODB_URI).get_default_database().users
    user_records = users.find({'user_id': {'$exists': True}}, {
        '_id': 0,
        'user_id': 1,
    })
    user_ids = [pid['user_id'] for pid in user_records]

    # Loop through user ids and update
    for user_id in user_ids:
        pm = PlaylistManager(user_id)
        updated = pm.update()
        if updated and pm.getmobileUpdateSetting() and pm.getMobileNumber() is not None:
            message = 'Your DWUnique has been updated!'
            message += f'\nCheck it out at https://play.spotify.com/user/dwunique/playlist/{pm.dwuId}'
            client.messages.create(to=pm.getMobileNumber(), from_=TWILIO_NUMBER, body=message)
