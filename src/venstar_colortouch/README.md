# Python3 API for Venstar ColorTouch API v5.

```Python
class Venstar:
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

