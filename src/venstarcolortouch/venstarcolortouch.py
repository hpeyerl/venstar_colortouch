import json
import requests
import urllib
import logging

MIN_API_VER=3

class VenstarColorTouch:
    def __init__(self, addr, timeout):
        self.MODE_OFF = 0
        self.MODE_HEAT = 1
        self.MODE_COOL = 2
        self.MODE_AUTO = 3
        self.STATE_IDLE = 0
        self.STATE_HEATING = 1
        self.STATE_COOLING = 2
        self.STATE_LOCKOUT = 3
        self.STATE_ERROR = 4
        self.FAN_AUTO = 0
        self.FAN_ON = 1
        self.FANSTATE_OFF = 0
        self.FANSTATE_ON = 1
        self.TEMPUNITS_F = 0
        self.TEMPUNITS_C = 1
        self.SCHED_F = 0
        self.SCHED_C = 1
        self.SCHEDPART_MORNING = 0
        self.SCHEDPART_DAY = 1
        self.SCHEDPART_EVENING = 2
        self.SCHEDPART_NIGHT = 3
        self.SCHEDPART_INACTIVE = 255
        self.AWAY_HOME = 0
        self.AWAY_AWAY = 1

        self.addr = addr
        self.timeout = timeout
        self.status = {}
        self._api_ver = None
        self._type = None
        self._info = None
        self._sensors = None
        #
        # /control
        #
        self.setpointdelta = None
        self.heattemp = None
        self.cooltemp = None
        self.fan = None
        self.mode = None
        #
        # /settings
        #
        self.tempunits = None
        self.away = None
        self.schedule = None
        self.hum_setpoint = None
        self.dehum_setpoint = None

        self.login()

    def login(self):
        r = self._request("/")
        if r is False:
            return r
        j = r.json()
        if j["api_ver"] >= MIN_API_VER:
            self._api_ver = j["api_ver"]
            self._type = j["type"]
            return True
        else:
            return False

    def _request(self, path, data=None):
        uri = "http://{addr}/{path}".format(addr=self.addr,path=path)
        try:
            if data is not None:
                req = requests.post(uri, timeout=self.timeout, data=data)
            else:
                req = requests.get(uri, timeout=self.timeout)
        except:
            print("Error requesting {uri} from Venstar ColorTouch".format(uri=uri))
            return False

        if not req.ok:
            print("Connection error logging into Venstar ColorTouch")
            return False

        return req

    def update_info(self):
        r = self._request("query/info")

        if r is False:
            return r

        self._info=r.json()
        #
        # Populate /control stuff
        #
        self.setpointdelta=self.get_info("setpointdelta")
        self.heattemp=self.get_info("heattemp")
        self.cooltemp=self.get_info("cooltemp")
        self.fan=self.get_info("fan")
        self.mode=self.get_info("mode")
        #
        # Populate /settings stuff
        #
        self.tempunits = self.get_info("tempunits")
        self.away = self.get_info("away")
        self.schedule = self.get_info("schedule")
        self.hum_setpoint = self.get_info("hum_setpoint")
        self.dehum_setpoint = self.get_info("dehum_setpoint")
        #
        return True

    def update_sensors(self):
        r = self._request("query/sensors")

        if r is False:
            return r
        self._sensors = r.json()
        return True

    def get_runtimes(self):
        r = self._request("query/runtimes")
        if r is False:
            return r
        else:
            runtimes=r.json()
            return runtimes["runtimes"][0]

    def get_info(self, attr):
        return self._info[attr]

    def get_thermostat_sensor(self, attr):
        return self._sensors["sensors"][0][attr]

    def get_outdoor_sensor(self, attr):
        return self._sensors["sensors"][1][attr]

    def get_alerts(self):
        r = self._request("query/alerts")
        if r is False:
            return r
        else:
            alerts=r.json()
            return alerts["alerts"][0]

    # The /control endpoint requires heattemp/cooltemp in each message, even if you're just turning
    # the fan on/off or setting the mode. So we retrieve everything from self and use accessors
    # to set them.
    def set_control(self):
        if self.mode is None:
            return False
        path="/control"
        data = urllib.urlencode({'mode':self.mode, 'fan':self.fan, 'heattemp':self.heattemp, 'cooltemp':self.cooltemp})
        print("Path is: {0}".format(path))
        r = self._request(path, data)
        if r is False:
            return r
        else:
            if r is not None:
                status = r.json()["success"]
                if status is True:
                    print("set_control Success!")
                else:
                    print("set_control Fail {0}.".format(r.json()))
                return status

    def set_setpoints(self, heattemp, cooltemp):
        # Must not violate setpointdelta.
        if heattemp + self.setpointdelta > cooltemp:
            return False
        self.heattemp = heattemp
        self.cooltemp = cooltemp
        return self.set_control()

    def set_mode(self, mode):
        self.mode = mode
        return self.set_control()

    def set_fan(self, fan):
        self.fan = fan
        return self.set_control()

    def set_settings(self):
        if self.tempunits is None:
            return False
        path="/settings"
        data = urllib.urlencode({'tempunits':self.tempunits, 'away':self.away, 'schedule':self.schedule, 'hum_setpoint':self.hum_setpoint, 'dehum_setpoint':self.dehum_setpoint})
        print("Path is: {0}".format(path))
        r = self._request(path, data)
        if r is False:
            return r
        else:
            if r is not None:
                status = r.json()["success"]
                if status is True:
                    print("set_control Success!")
                else:
                    print("set_control Fail {0}.".format(r.json()))
                return status

    def set_tempunits(self, tempunits):
        self.tempunits = tempunits
        return self.set_settings()

    def set_away(self, away):
        self.away = away
        return self.set_settings()

    def set_schedule(self, schedule):
        self.schedule = schedule
        return self.set_settings()

    def set_hum_setpoint(self, hum_setpoint):
        self.hum_setpoint = hum_setpoint
        return self.set_settings()

    def set_dehum_setpoint(self, dehum_setpoint):
        self.dehum_setpoint = dehum_setpoint
        return self.set_settings()
