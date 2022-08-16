import json
import requests
import urllib3
import urllib
import logging
from requests.auth import HTTPDigestAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MIN_API_VER=3
# Venstar developers fixed a bug for some models with the 5.28 firmware
#   version. The new firmware correctly reports temperatures in the
#   configured temperature unit.
UNIT_BUG_FIX_VERSION = (5, 28)

class VenstarColorTouch:
    def __init__(self, addr, timeout, user=None, password=None, pin=None, proto='http', SSLCert=False):
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
        self.SECURITY_OFF = 0
        self.SECURITY_ON = 1
        self.SCHED_F = 0
        self.SCHED_C = 1
        self.SCHEDPART_MORNING = 0
        self.SCHEDPART_DAY = 1
        self.SCHEDPART_EVENING = 2
        self.SCHEDPART_NIGHT = 3
        self.SCHEDPART_INACTIVE = 255
        self.AWAY_HOME = 0
        self.AWAY_AWAY = 1

        self.sensor_names = { "Control": [ "Space Temp" ], "Local": [ "Thermostat" ] }
        self.sensor_types = [ "Control", "Local", "Outdoor", "Remote", "Return", "Supply" ]

        #Input parameters
        self.addr = addr
        self.timeout = timeout

        #Use Python standard logging class
        self.log = logging.getLogger(__name__)

        #Preprocess authentication related parameters
        if pin is not None:
            self.pin = str(pin).zfill(4)
        else:
            self.pin = None

        if user != None and password != None:
            self.auth = HTTPDigestAuth(user, password)
        else:
            self.auth = None

        self.proto = proto
        self.SSLCert = SSLCert

        #Initialize State
        self.status = {}
        self.model = None
        self._api_ver = None
        self._type = None
        self._info = None
        self._sensors = None
        self._firmware_ver = None
        self.alerts = None
        self.runtimes = None
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
        self.security = None
        self.sp_min = None
        self.sp_max = None

    def login(self):
        r = self._request("/")
        if r is False:
            self.log.error("Failed to request thermostat info in login")
            return r
        j = r.json()
        if j["api_ver"] >= MIN_API_VER:
            self._api_ver = j["api_ver"]
            if "firmware" in j:
                self._firmware_ver = tuple(map(int, j["firmware"].split(".")))
            else:
                self._firmware_ver = (0,0)
            logging.debug("api_ver: %s" % self._api_ver)
            self._type = j["type"]
            if "model" in j:
                self.model = j["model"]
            else:
                self.model = "COLORTOUCH"
            return True
        else:
            self.log.error("Unsupported API version: %s", j["api_ver"])
            return False

    def _request(self, path, data=None):
        # All calls to _request must have leading slash in path
        uri = "{proto}://{addr}{path}".format(proto=self.proto, addr=self.addr, path=path)
        params = {}
        if self.pin:
            params['pin'] = self.pin
        try:
            if data is not None:
                req = requests.post(uri,
                                    verify=self.SSLCert,
                                    timeout=self.timeout,
                                    data=data,
                                    params=params,
                                    auth=self.auth)
            else:
                req = requests.get(uri,
                                   verify=self.SSLCert,
                                   timeout=self.timeout,
                                   params=params,
                                   auth=self.auth)
        except Exception as ex:
            self.log.exception("Error requesting {uri} from Venstar ColorTouch.".format(uri=uri))
            return False

        if not req.ok:
            self.log.error("Connection error logging into Venstar ColorTouch. Status Code: {status}".format(status=req.status_code))
            return False

        return req

    def update(self, alerts = True, info = True, runtimes = True, sensors = True):
        if alerts:
            if not self.update_alerts():
                return False
        if info:
            if not self.update_info():
                return False
        if runtimes:
            if not self.update_runtimes():
                return False
        if sensors:
            if not self.update_sensors():
                return False
        return True

    def update_info(self):
        # Model number (set during login) *required* for this function
        if self.model is None:
            self.log.debug("update_info() called without login(), executing login()")
            if not self.login():
                self.log.error("Login failed during update_info() call!")
                return False

        r = self._request("/query/info")

        if r is False:
            return r

        try:
            self._info=r.json()
        except json.decoder.JSONDecodeError as error:
            self.log.error("Failed to decode JSON: %s", error.msg)
            return False

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
        self.display_tempunits = self.get_settings("tempunits")
        if self._type != "commercial":  #Commercial thermostats don't support "away"
          self.away = self.get_settings("away")
        self.schedule = self.get_settings("schedule")
        self.hum_setpoint = self.get_settings("hum_setpoint")
        self.dehum_setpoint = self.get_settings("dehum_setpoint")
        #
        if "hum_active" in self._info:
            self.hum_active = self.get_info("hum_active")
        else:
            self.hum_active = 0
        self.sp_min = self.get_info("cooltempmin")
        self.sp_max = self.get_info("heattempmax")

        #
        # T2xxx, T3xxx thermostats with firmware < 5.28 always use Celsius in the
        # API regardless of the display units, so handle this case accordingly
        if self.model.startswith(("T2", "T3")) and self.get_firmware_ver() < UNIT_BUG_FIX_VERSION:
            # Always degC for firmware <= 5.28
            self.tempunits = self.TEMPUNITS_C
            logging.debug("Detected thermostat model %s, using temp units of Celsius", self.model)
        elif (self.model in ["VYG-4900-VEN", "VYG-4800-VEN", "VYG-3900", "COLORTOUCH"] or
              self.model.startswith(("T2", "T3"))):
            # Same as display units
            self.tempunits = self.display_tempunits
        elif self.get_info("heattempmax") >= 40:
            # Heat max temp over 40, only possible if degF
            logging.warning("Unknown thermostat model %s, inferring API tempunits of Fahrenheit", self.model)
            self.tempunits = self.TEMPUNITS_F
        else:
            logging.warning("Unknown thermostat model %s, inferring API tempunits of Celsius", self.model)
            self.tempunits = self.TEMPUNITS_C
        return True

    def update_sensors(self):
        r = self._request("/query/sensors")
        if r is False:
            return r
        self._sensors = r.json()
        return True

    # returns a list of all runtime records. get_runtimes()[-1] should be the last one.
    # runtimes are updated every day (86400 seconds).
    def get_runtimes(self):
        r = self._request("/query/runtimes")
        if r is False:
            return r
        else:
            runtimes=r.json()
            return runtimes["runtimes"]

    def update_runtimes(self):
        self.runtimes = self.get_runtimes()
        if self.runtimes:
            return True
        return False

    def get_info(self, attr):
        return self._info[attr]

    def get_settings(self, attr):
        if attr in self._info:
            return self.get_info(attr)

        # some models only return settings at this endpoint
        r = self._request(f"/settings?q={attr}") 
        if not r:
            return None

        setting = r.json().get(attr)
        self._info[attr] = setting

        return setting

    def get_api_ver(self):
        return self._api_ver

    def get_firmware_ver(self):
        return self._firmware_ver

    def get_type(self):
        return self._type

    def get_sensor(self, name, attr):
        if self._sensors != None and self._sensors["sensors"] != None and len(self._sensors["sensors"]) > 0:
            for sensor in self._sensors["sensors"]:
                # 'hum' (humidity) sensor is not present on T5800 series
                if "name" in sensor and sensor["name"] == name and attr in sensor:
                    return sensor[attr]
                elif "name" in sensor and sensor["name"] == name and attr not in sensor and attr == "type" and sensor["name"] in self.sensor_types:
                    return sensor["name"]
                elif "name" in sensor and sensor["name"] == name and attr not in sensor and attr == "type" and sensor["name"] in self.sensor_names["Control"]:
                    return "Control"
                elif "name" in sensor and sensor["name"] == name and attr not in sensor and attr == "type" and sensor["name"] in self.sensor_names["Local"]:
                    return "Local"
        return None

    def get_sensor_list(self, type=None):
        names = [];
        if self._sensors != None and self._sensors["sensors"] != None and len(self._sensors["sensors"]) > 0:
            for sensor in self._sensors["sensors"]:
                if "name" in sensor:
                    if type != None:
                        if "type" in sensor and sensor["type"] == type:
                            names.append(sensor["name"])
                        elif type not in sensor and sensor["name"] in self.sensor_types and sensor["name"] == type:
                            names.append(sensor["name"])
                        elif type not in sensor and sensor["name"] in self.sensor_names["Control"] and type == "Control":
                            names.append(sensor["name"])
                        elif type not in sensor and sensor["name"] in self.sensor_names["Local"]  and type == "Local":
                            names.append(sensor["name"])
                    else:
                        names.append(sensor["name"])
        return names

    def get_thermostat_sensor(self, attr):
        sensors = self.get_sensor_list("Local")
        if len(sensors) > 0:
            return self.get_sensor(sensors[0], attr)
        return None

    def get_outdoor_sensor(self, attr):
        sensors = self.get_sensor_list("Outdoor")
        if len(sensors) > 0:
            return self.get_sensor(sensors[0], attr)
        return None

    def get_indoor_temp(self):
        sensors = self.get_sensor_list("Control") + self.get_sensor_list("Local")
        if len(sensors) > 0:
            return self.get_sensor(sensors[0], "temp")
        return None

    def get_outdoor_temp(self):
        return self.get_outdoor_sensor("temp")

    def get_indoor_humidity(self):
        return self.get_thermostat_sensor("hum")

    def get_alerts(self):
        r = self._request("/query/alerts")
        if r is False:
            return r
        else:
            alerts=r.json()
            return alerts["alerts"]

    def update_alerts(self):
        self.alerts = self.get_alerts()
        if self.alerts:
            return True
        return False

    def parse_response(self, r, setting, update_info=False):
        if r is False or r is None:
            return False
        else:
            try:
                if "success" in r.json():
                    self.log.debug("{0} Success!".format(setting))
                    if update_info:
                        self.update_info()
                    return True
                else:
                    self.log.error("{0} Fail {1}.".format(setting, r.text))
                    return False
            except json.decoder.JSONDecodeError as error:
                self.log.error("Failed to decode JSON: %s", error.msg)
                return False

    def set_control(self, data):
        path="/control"
        r = self._request(path, data)
        return self.parse_response(r, 'set_control')

    # When setting MODE, you must also set heattemp/cooltemp.
    # The set of legal operations is:
    # When setting fan, only set fan.
    # When setting heat/cool, set both heat cool and nothing else.
    # When setting mode, set mode, heat and cool.

    def set_setpoints(self, heattemp, cooltemp):
        # Must not violate setpointdelta if we're in auto mode.
        if self.mode == self.MODE_AUTO and heattemp + self.setpointdelta > cooltemp:
            self.log.warning("In auto mode, the cool temp must be {0} "
                  "degrees warmer than the heat temp.".format(self.setpointdelta))
            return False
        self.heattemp = heattemp
        self.cooltemp = cooltemp
        data = urllib.parse.urlencode({'heattemp':self.heattemp, 'cooltemp':self.cooltemp})
        return self.set_control(data)

    def set_mode(self, mode):
        self.mode = mode
        data = urllib.parse.urlencode({'mode': self.mode, 'heattemp':self.heattemp, 'cooltemp':self.cooltemp})
        return self.set_control(data)

    def set_fan(self, fan):
        self.fan = fan
        data = urllib.parse.urlencode({'fan': self.fan})
        return self.set_control(data)

    #
    # set_settings can't change the schedule or away while schedule is on, so no point in trying.
    #
    def set_settings(self):
        if self.tempunits is None:
            self.log.error("update_info() must be called before settings may be set, aborting!")
            return False
        path="/settings"
        data = urllib.parse.urlencode({'tempunits':self.display_tempunits, 'hum_setpoint':self.hum_setpoint, 'dehum_setpoint':self.dehum_setpoint})
        r = self._request(path, data)
        return self.parse_response(r, 'set_settings', update_info=True)

    def set_security(self, security):
        if security not in [self.SECURITY_ON, self.SECURITY_OFF]:
            return False
        path = "/settings"
        data = urllib.parse.urlencode({'security': security})
        r = self._request(path, data)
        self.security = security
        return self.parse_response(r, 'set_security')

    def set_setpoint_limits(self, sp_max=None, sp_min=None):
        if (sp_max == self.sp_max and sp_min == self.sp_min) or (sp_max is None and sp_min is None):
            return True
        path = "/settings"
        # Make sure security is on
        if self.security == 0:
            self.set_security(1)
        sp_limit_data = {}
        if sp_max is not None:
            sp_limit_data['spMax'] = sp_max
        if sp_min is not None:
            sp_limit_data['spMin'] = sp_min
        data = urllib.parse.urlencode(sp_limit_data)
        r = self._request(path, data)
        return self.parse_response(r, 'set_setpoint_limits', update_info=True)

    def set_tempunits(self, tempunits):
        self.tempunits = tempunits
        return self.set_settings()

    def set_away(self, away):
        if self.away is None:
            self.log.error("update_info() must be called before away mode may be changed, aborting!")
            return False
        if not self._type.lower() == "residential":
            self.log.error("Away mode is not supported on commercial thermostat models.")
            return False

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
        return self.parse_response(r, 'set_away', update_info=True)

    #
    # We can't change any settings while the schedule is active so we can't use set_settings()
    #
    def set_schedule(self, schedule):
        if self.schedule is None:
            self.log.error("update_info() must be called before schedule state may be changed, aborting!")
            return False

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
        return self.parse_response(r, 'set_schedule', update_info=True)

    def set_hum_setpoint(self, hum_setpoint):
        if self.hum_setpoint is None:
            self.log.warning("No humidifier support detected, ignoring set_hum_setpoint call!")
            return False
        self.hum_setpoint = hum_setpoint
        return self.set_settings()

    def set_dehum_setpoint(self, dehum_setpoint):
        if self.dehum_setpoint is None:
            self.log.warning("No dehumidification control support detected, ignoring set_dehum_setpoint call!")
            return False
        self.dehum_setpoint = dehum_setpoint
        return self.set_settings()
