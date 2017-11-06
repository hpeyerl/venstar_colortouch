# Python3 API for Venstar ColorTouch thermostats

The [Venstar ColorTouch thermostat](https://venstar.com/thermostats/colortouch/) is a WIFI thermostat with a REST api.  This is a simple Python3 API for talking to it.

## Limitations

```Python
class VenstarColorTouch:
    def __init__(self, addr, timeout):
```

Class instantiation requires an IP address or hostname with an optional timeout.

## API

