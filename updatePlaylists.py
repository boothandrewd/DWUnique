""" app/updatePlaylists.py
Script issued by Heroku Scheduler to update DwUniques.
"""
import os
from datetime import date
import time

from pymongo import MongoClient

from app.ArchiveManager import ArchiveManager
from app.utils import send_sms, date_to_week

archives = MongoClient(os.environ['MONGODB_URI']).DwUnique.archives
playlist_id_dicts = list(archives.find({'playlist_id': {'$exists': True}}, {
    '_id': 0,
    'playlist_id': 1
}))

# Only update on Mondays
if date.today().weekday() == 0:
    start_time = time.time()
    # Loop over playlist_ids until they've all been updated
    playlist_ids = [pid['playlist_id'] for pid in playlist_id_dicts]
    while playlist_ids:
        if time.time() - start_time > 60*15:
            break
        for playlist_id in list(playlist_ids):
            am = ArchiveManager(playlist_id)

            if not am.updatedThisWeek():
                if am.playlistIsNew():
                    playlist_ids.remove(playlist_id)
                    mobile_number = am.getMobileNumber()
                    if mobile_number:
                        send_sms(mobile_number, 'Your DWUnique has been updated!')

            else:
                playlist_ids.remove(playlist_id)


            # # Only perform update if different week
            # today_string = today_as_string()
            # cpd = am.getDwUniqueDate()
            # if cpd == '' or date_to_week(today_string) != date_to_week(cpd):
            #     # If there was an update, remove from update list and alert user
            #     if am.update():
            #         playlist_ids.remove(playlist_id)
            #         mobile_number = am.getMobileNumber()
            #         if mobile_number:
            #             send_sms(mobile_number, 'Your DWUnique has been updated!')
            #
            #
            # # # Otherwise same week, so remove from update list
            # # else:
            # #     playlist_ids.remove(playlist_id)
