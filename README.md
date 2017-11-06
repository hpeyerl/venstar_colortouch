# Python3 API for QuickSmart Etherrain/8

The EtherRain/8 from [QuickSmart](http://www.quicksmart.com/qs_etherrain.html) is an Ethernet based irrigation controller with a custom web API.  This is a simple Python3 API for talking to it.

## Limitations
* The ER8 maintains its authentication state by IP address.  So if another process or client on your system has authenticated with the ER8, then the login() function will succeed even with an invalid password.
* Due to the above limitation, a client with an invalid username/password on the same host can issue watering commands and retrieve state, etc.
* This API Assumes an Etherrain/8 and doesn't anticipate anything as regards the Etherrain/7P

```Python
class EtherRain:
    def __init__(self, addr, user, pw, timeout):
```

Class instantiation requires an IP address or hostname, username, and password with an optional timeout.

## API
* login() -  Authenticate.  Returns true or false
* stop() -  Full stop to all watering operations
* update_status() - Call this before checking the operating status or any other status attributes.
* get_status() - Return the current operating status. Call ```update_status()``` first.  Returns:
  * BZ - Busy
  * WT - Waiting
  * RD - Ready
* rain() - Is the rain sensor reporting that it is wet?
* last_valve() - Returns which valve is currently turned on or has more recently been turned on.  Returns 0-8
* irrigate(valve, time) - Turn on an irrigation valve. Time is in Minutes.  Valve is 1-8.

