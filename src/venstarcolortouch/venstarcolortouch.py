import json
import requests
import urllib3
import urllib
import logging
from requests.auth import HTTPDigestAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MIN_API_VER=3

class VenstarColorTouch:
    def __init__(self, addr, timeout, user=None, password=None, proto='http', SSLCert=False):
        #API Constants
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

        #Input parameters
        self.addr = addr
        self.timeout = timeout

        if user != None and password != None:
            self.auth = HTTPDigestAuth(user, password)
        else:
            self.auth = None

        self.proto = proto 
        self.SSLCert = SSLCert

        #Initialize State
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
        self.fanstate = None
        self.state = None
        #
        # /settings
        #
        self.name = None
        self.tempunits = None
        self.away = None
        self.schedule = None
        self.hum_setpoint = None
        self.dehum_setpoint = None
        self.hum_active = None

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
        uri = "{proto}://{addr}/{path}".format(proto=self.proto, addr=self.addr, path=path)
        try:
            if data is not None:
                req = requests.post(uri, 
                                    verify=self.SSLCert,
                                    timeout=self.timeout,
                                    data=data,
                                    auth=self.auth)
            else:
                req = requests.get(uri,
                                   verify=self.SSLCert,
                                   timeout=self.timeout,
                                   auth=self.auth)
        except Exception as ex:
            print("Error requesting {uri} from Venstar ColorTouch.".format(uri=uri))
            print(ex)
            return False

        if not req.ok:
            print("Connection error logging into Venstar ColorTouch. Status Code: {status}".format(status=req.status_code))
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
        self.fanstate=self.get_info("fanstate")
        self.mode=self.get_info("mode")
        self.state=self.get_info("state")

        #
        # Populate /settings stuff
        #
        self.name = self.get_info("name")
        self.tempunits = self.get_info("tempunits")
        self.away = self.get_info("away")
        self.schedule = self.get_info("schedule")
        # T5800 thermostat will not have hum_setpoint/dehum_setpoint in the JSON, so make
        # it optional
        if 'hum_setpoint' in self._info:
          self.hum_setpoint = self.get_info("hum_setpoint")
        else:
          self.hum_setpoint = None
        if 'dehum_setpoint' in self._info:
          self.dehum_setpoint = self.get_info("dehum_setpoint")
        else:
          self.dehum_setpoint = None
        #
        if 'hum_active' in self._info:
            self.hum_active = self.get_info("hum_active")
        else:
            self.hum_active = 0

        return True

    def update_sensors(self):
        r = self._request("query/sensors")

        if r is False:
            return r
        self._sensors = r.json()
        return True

    # returns a list of all runtime records. get_runtimes()[-1] should be the last one.
    # runtimes are updated every day (86400 seconds).
    def get_runtimes(self):
        r = self._request("query/runtimes")
        if r is False:
            return r
        else:
            runtimes=r.json()
            return runtimes["runtimes"]

    def get_info(self, attr):
        return self._info[attr]

    def get_thermostat_sensor(self, attr):
        if self._sensors != None and self._sensors["sensors"] != None and len(self._sensors["sensors"]) > 0:
            # 'hum' (humidity) sensor is not present on T5800 series
            if attr in self._sensors["sensors"][0]:
              return self._sensors["sensors"][0][attr]
            else:
              return None
        else:
            return None

    def get_outdoor_sensor(self, attr):
        if self._sensors != None and self._sensors["sensors"] != None and len(self._sensors["sensors"]) > 0:
            return self._sensors["sensors"][1][attr]
        else:
            return None

    def get_indoor_temp(self):
        return self.get_thermostat_sensor('temp')

    def get_outdoor_temp(self):
        return self.get_outdoor_sensor('temp')

    def get_indoor_humidity(self):
        return self.get_thermostat_sensor('hum')

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
        data = urllib.parse.urlencode({'mode':self.mode, 'fan':self.fan, 'heattemp':self.heattemp, 'cooltemp':self.cooltemp})
        r = self._request(path, data)
        if r is False:
            return r
        else:
            if r is not None:
                if "success" in r.json():
                    print("set_control Success!")
                    return True
                else:
                    print("set_control Fail {0}.".format(r.json()))
                    return False

    def set_setpoints(self, heattemp, cooltemp):
        # Must not violate setpointdelta if we're in auto mode.
        if self.mode == self.MODE_AUTO and heattemp + self.setpointdelta > cooltemp:
            print("In auto mode, the cool temp must be {0} " 
                  "degrees warmer than the heat temp.".format(self.setpointdelta))
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

    #
    # set_settings can't change the schedule or away while schedule is on, so no point in trying.
    #
    def set_settings(self):
        if self.tempunits is None:
            return False
        path="/settings"
        data = urllib.parse.urlencode({'tempunits':self.tempunits, 'hum_setpoint':self.hum_setpoint, 'dehum_setpoint':self.dehum_setpoint})
        r = self._request(path, data)
        if r is False:
            return r
        else:
            if r is not None:
                if "success" in r.json():
                    print("set_settings Success!")
                    return True
                else:
                    print("set_settings Fail {0}.".format(r.text))
                    return False

    def set_tempunits(self, tempunits):
        self.tempunits = tempunits
        return self.set_settings()

    def set_away(self, away):
        if self.away == away:
            return True
        if self.schedule == 1:
            ret = self.set_schedule(0)
            if ret == False:
                return ret
        self.away = away
        path="/settings"
        data = urllib.parse.urlencode({'away':self.away})
        r = self._request(path, data)
        if r is False:
            ret = False
        else:
            if r is not None:
                if "success" in r.json():
                    print("set_away Success!")
                    self.update_info()
                    ret = True
                else:
                    print("set_away Fail {0}.".format(r.json()))
                    ret = False
        return ret

    #
    # We can't change any settings while the schedule is active so we can't use set_settings()
    #
    def set_schedule(self, schedule):
        if (self.schedule == schedule):
            return True
        #
        # If thermostat is in away mode, then can't enable schedule.
        #
        if (self.away == 1):
            return False
        self.schedule = schedule
        path="/settings"
        data = urllib.parse.urlencode({'schedule':self.schedule})
        r = self._request(path, data)
        if r is False:
            ret = False
        else:
            if r is not None:
                if "success" in r.json():
                    print("set_schedule Success!")
                    self.update_info()
                    ret = True
                else:
                    print("set_schedule Fail {0}.".format(r.json()))
                    ret = False
        return ret

    def set_hum_setpoint(self, hum_setpoint):
        self.hum_setpoint = hum_setpoint
        return self.set_settings()

    def set_dehum_setpoint(self, dehum_setpoint):
        self.dehum_setpoint = dehum_setpoint
        return self.set_settings()
