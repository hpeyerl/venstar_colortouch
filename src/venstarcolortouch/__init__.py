import sys

__version__ = "0.8"

__uri__ = 'https://github.com/hpeyerl/venstarcolortouch'
__title__ = "venstarcolortouch"
__description__ = 'Interface Library for Venstar ColorTouch Thermostat API v5'
__doc__ = __description__ + " <" + __uri__ + ">"
__author__ = 'Herb Peyerl'
__email__ = 'hpeyerl+venstar@beer.org'
__license__ = "MIT"

__copyright__ = "Copyright (c) 2017 Herb Peyerl"

from .venstarcolortouch import VenstarColorTouch

if __name__ == '__main__': print(__version__)
