""" app/utils.py
"""
import re

from twilio.rest import TwilioRestClient

client = TwilioRestClient(os.environ['ACCOUNT_SID'], os.environ['AUTH_TOKEN'])
TWILIO_NUMBER = os.environ['TWILIO_NUMBER']

# Playlist parsing resource function
def parse_playlist_resource(resource):
    delimiter = '/'
    if resource.startswith('spotify'):
        delimiter = ':'
    return resource.split(delimiter)[-1]

# Mobile number checking function
def clean_mobile_number(mobile_number):
    return re.sub(r'\D', '', mobile_number)

# Hash checking function
def is_hash(candidate):
    return not re.search(r'\W', candidate)

# Text sending function
def send_sms(mobile_number, message):
    sms = client.messages.create(
        to=mobile_number,
        from_=TWILIO_NUMBER,
        body=message
    )
