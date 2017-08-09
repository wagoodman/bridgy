import collections
import inquirer
import logging
import sys
import os

logger = logging.getLogger()

class color:
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    RED = '\033[91m'
    UNDERLINE = '\033[4m'
    NORMAL = '\033[0m'
    BOLD = '\033[1m'

class UnsupportedPlatform(Exception): pass

def platform():
    from sys import platform as _platform

    if 'linux' in _platform:
        return 'linux'
    elif 'darwin' in  _platform:
        return 'osx'
    elif 'win' in _platform:
        return 'windows'
    return _platform

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
