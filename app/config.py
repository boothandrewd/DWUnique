""" app/config.py
"""
import os

# Flask vars
DEBUG = os.environ['DEBUG']

if 'SECRET_KEY' in os.environ:
    SECRET_KEY = os.environ['SECRET_KEY']
else:
    SECRET_KEY = os.urandom(24)

# Other vars
if 'APP_URL'in os.environ:
    APP_URL = os.environ['APP_URL']
else:
    APP_URL = f'https://{os.environ["HEROKU_APP_NAME"]}.herokuapp.com'

SPOTIPY_REDIRECT_URI = os.path.join(APP_URL, 'spotify-auth-callback')
