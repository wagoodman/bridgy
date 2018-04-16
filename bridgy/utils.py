import logging
import uuid
import sys
import os
import re

from blessings import Terminal

term = Terminal()
logger = logging.getLogger()


class UnsupportedPlatform(Exception): pass

def platform():

    if 'linux' in sys.platform:
        return 'linux'
    elif 'darwin' in  sys.platform:
        return 'osx'
    elif 'win' in sys.platform:
        return 'windows'
    return sys.platform

class SupportedPlatforms(object):
    def __init__(self, *platforms):
        self.platforms = platforms

    def __call__(self, func):
        decorator_self = self
        def wrapper(*args, **kwargs):
            decorator_self.check_supported_platforms()
            func(*args,**kwargs)
        return wrapper

    def check_supported_platforms(self):
        normalized = platform()

        if normalized not in self.platforms:
            raise UnsupportedPlatform('Unsupported platform (%s)' % normalized)

def shortUuid():
    return str(uuid.uuid4())[:8]

def memoize(f):
    class memodict(dict):
        def __init__(self, f):
            self.f = f
        def __call__(self, *args):
            return self[args]
        def __missing__(self, key):
            ret = self[key] = self.f(*key)
            return ret
    return memodict(f)

def parseIpFromHostname(hostname):
    match = re.search(r'\d{1,3}[\.\-\_]{1}\d{1,3}[\.\-\_]{1}\d{1,3}[\.\-\_]{1}\d{1,3}', hostname)
    if match:
        return match.group().replace('-', '.').replace('_', '.')
