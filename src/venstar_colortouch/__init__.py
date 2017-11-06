import sys

__version__ = "0.1"

__uri__ = 'https://github.com/hpeyerl/venstar_colortouch'
__title__ = "venstar_colortouch"
__description__ = 'Interface Library for Venstar ColorTouch Thermostat API v5'
__doc__ = __description__ + " <" + __uri__ + ">"
__author__ = 'Herb Peyerl'
__email__ = 'hpeyerl+venstar@beer.org'
__license__ = "MIT"

__copyright__ = "Copyright (c) 2017 Herb Peyerl"

from .venstar import VenstarColorTouch

if __name__ == '__main__': print(__version__)
