""" app/config.py
"""
import os
DEBUG = os.environ['DEBUG']

if 'SECRET_KEY' in os.environ:
    SECRET_KEY = os.environ['SECRET_KEY']
else:
    SECRET_KEY = os.urandom(24)
