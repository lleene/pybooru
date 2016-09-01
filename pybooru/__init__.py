# -*- coding: utf-8 -*-

"""
Pybooru
-------

Pybooru is a Python library to access API of Moebooru based sites.
Under MIT license.

Pybooru requires "requests" package to work.

Pybooru modules:
    pybooru -- Main module of Pybooru, contains Pybooru class.
    moebooru -- Contains Moebooru main class.
    danbooru -- Contains Danbooru main class.
    api_moebooru -- Contains all Moebooru API functions.
    api_danbooru -- Contains all Danbooru API functions.
    exceptions -- Manages and builds Pybooru errors messages.
    resources -- Contains all resources for Pybooru.
"""

__version__ = "3.0.1"
__license__ = "MIT"
__url__ = "http://github.com/LuqueDaniel/pybooru"
__author__ = "Daniel Luque <danielluque14@gmail.com>"

# pybooru imports
from .moebooru import Moebooru
from .danbooru import Danbooru
from .exceptions import PybooruError
