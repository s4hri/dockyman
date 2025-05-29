import os

VERSION_PATH = os.path.join(os.path.dirname(__file__), 'VERSION')

with open(VERSION_PATH, 'r') as f:
    __version__ = f.read().strip()