""" app/updatePlaylists.py
Script issued by Heroku Scheduler to update DwUniques.
"""
import os
from datetime import date
import time

from pymongo import MongoClient

from app.ArchiveManager import ArchiveManager
from app.utils import send_sms, date_to_week

archives = MongoClient(os.environ['MONGODB_URI']).get_default_database().archives

playlist_id_dicts = list(archives.find({'playlist_id': {'$exists': True}}, {
    '_id': 0,
    'playlist_id': 1
}))

# Only update on Mondays
if date.today().weekday() == 0:
    # Get start time
    start_time = time.time()

    # Loop over playlist_ids until they've all been updated
    playlist_ids = [pid['playlist_id'] for pid in playlist_id_dicts]
    while len(playlist_ids) != 0:
        # If trying for 15 minutes, quit
        if time.time() - start_time > 60*15:
            break

        # For the playlists still in the list,
        for playlist_id in list(playlist_ids):
            am = ArchiveManager(playlist_id)

            # If the playlist hasn't been updated
            if not am.updatedThisWeek():
                # If there are new songs
                if am.playlistIsNew():
                    # Update, remove, and send update text
                    am.update()
                    playlist_ids.remove(playlist_id)
                    mobile_number = am.getMobileNumber()
                    if mobile_number:
                        message = 'Your DWUnique has been updated!'
                        message += '\nAnd there were some songs filtered!' if am.songsWereFiltered() else ''
                        message += '\nCheck it out at %s/playlist/%s' % (os.environ['APP_URL'], playlist_id)
                        send_sms(mobile_number, message)

            # Remove playlist from list if it's been updated this week
            else:
                playlist_ids.remove(playlist_id)
