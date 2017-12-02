# Python3 API for Venstar ColorTouch thermostats

The [Venstar ColorTouch thermostat](https://venstar.com/thermostats/colortouch/) is a WIFI thermostat with a REST api.  This is a simple Python3 API for talking to it.  The [API documents](http://developer.venstar.com/index.html) are required reading.

## Limitations

The API does not implement the Venstar discovery protocol.  It is assumed that you know the IP address or FQDN of your thermostat(s).

## Testing

```bash
$ python venstarcolortouch 192.168.1.252
Testing with IP: 192.168.1.252
Login successful. API: 5 Type: residential
Was able to get info:{u'spacetemp': 67.0, u'schedulepart': 255, u'dehum_setpoint': 0, u'away': 0, u'cooltempmax': 99.0, u'cooltemp': 78.0, u'tempunits': 0, u'state': 1, u'schedule': 0, u'hum': 0, u'heattemp': 75.0, u'hum_setpoint': 36, u'fan': 0, u'hum_active': 99, u'heattempmax': 99.0, u'cooltempmin': 35.0, u'name': u'DebtRidge', u'mode': 1, u'heattempmin': 35.0, u'availablemodes': 0, u'fanstate': 1, u'setpointdelta': 2.0}
Name is MyHouse
Fan is 0
Heat setpoint is 75.0
Cool setpoint is 78.0

Was able to get sensors:{u'sensors': [{u'hum': 36, u'name': u'Thermostat', u'temp': 67.0}, {u'name': u'Outdoor', u'temp': 0.0}]}
Indoor temp is 67.0 and humidity is 36
Runtimes: {u'cool1': 0, u'cool2': 0, u'ts': 1429574400, u'fc': 0, u'heat2': 0, u'heat1': 0, u'aux2': 0, u'aux1': 0}
Path is: /control
set_control Success!
Heat setpoint is 60.0
Cool setpoint is 90.0

Path is: /control
set_control Success!
Heat setpoint is 75.0
Cool setpoint is 78.0
```

## Usage
```Python
class VenstarColorTouch:
    def __init__(self, addr, timeout):
```

Class instantiation requires an IP address or hostname with an optional timeout.


```Python
    ct = venstarcolortouch.VenstarColorTouch(a, timeout=5)

    if ct.login() is True:
        print("Login successful. API: {0} Type: {1}".format(ct._api_ver,ct._type))
```

The login() function does not really log in, but it does confirm communication and that the API version is recent enough.

## API

API calls use the following constants:

```Python
MODE_OFF
MODE_HEAT
MODE_COOL
MODE_AUTO
STATE_IDLE
STATE_HEATING
STATE_COOLING
STATE_LOCKOUT
STATE_ERROR
FAN_AUTO
FAN_ON
FANSTATE_OFF
FANSTATE_ON
TEMPUNITS_F
TEMPUNITS_C
SCHED_F
SCHED_C
SCHEDPART_MORNING
SCHEDPART_DAY
SCHEDPART_EVENING
SCHEDPART_NIGHT
SCHEDPART_INACTIVE
AWAY_HOME
AWAY_AWAY
```

### Functions

There are ```update_*``` functions which update local copies of various pieces of data.  Then there are ```get_*``` functions for retrieving that data and finally ```set_*``` functions for changing writable settings.

* ```update_sensors()``` - Update the state of indoor and outdoor temperature sensors.

* ```get_runtimes()``` - Gather runtime data.

* ```get_info()``` - returns a dict of information.
    <pre>
    {u'spacetemp',
     u'schedulepart',
     u'dehum_setpoint',
     u'away',
     u'cooltempmax',
     u'cooltemp',
     u'tempunits',
     u'state',
     u'schedule',
     u'hum',
     u'heattemp',
     u'hum_setpoint',
     u'fan',
     u'hum_active',
     u'heattempmax',
     u'cooltempmin',
     u'name',
     u'mode',
     u'heattempmin',
     u'availablemodes',
     u'fanstate',
     u'setpointdelta'}
    </pre>

    ```python
    get_info("heattemp")
    ```
    
*  ```get_thermostat_sensor(attr)``` Get a specific thermostat sensor's value.
    
    ```python
    get_thermostat_sensor("temp")
    ```

* ```get_outdoor_sensor(attr)``` Get an outdoor sensor's value.

    ```python
    get_outdoor_sensor("temp")```

* ```get_alerts()``` Get any alerts that are registered.

* ```set_setpoints(heattemp, cooltemp)``` Set heattemp/cooltemp.

* ```set_mode(mode)``` Set the thermostat mode.
    * MODE_OFF
    * MODE_HEAT
    * MODE_COOL
    * MODE_AUTO

* ```set_fan(fan)``` Set the Fan mode.
    * FAN_AUTO
    * FAN_ON

* ```set_tempunits(tempunits)``` Set degrees to either Celsius or Fahrenheit
    * TEMPUNITS_F
    * TEMPUNITS_C
* ```set_away(away)``` Set either Home or Away schedule.
    * AWAY_HOME
    * AWAY_AWAY
* ```set_schedule(schedule)``` Set Schedule On or Off.
    * 0 - off
    * 1 - on
* ```set_hum_setpoint(hum_setpoint)``` Set humidifier Setpoint
* ```set_dehum_setpoint(dehum_setpoint)``` Set dehumidifier Setpoint

