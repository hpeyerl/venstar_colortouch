import json
import requests
import logging

MIN_API_VER=3

class VenstarColorTouch:
    def __init__(self, addr, timeout):
        self.addr = addr
        self.timeout = timeout
        self.status = {}
        self._api_ver, self._type = 
        self._type = None
        self._info = None
        self._sensors = None
        self.login()

    def login(self):
        r = self._request("/")
        j = r.json()
        if j["api_ver"] >= MIN_API_VER:
            self._api_ver = j["api_ver"]
            self._type = j["type"]
            return True
        else:
            return False

    def _request(self, uri):
        try:
            req = requests.get(uri, timeout=self.timeout)
        except BadStatusLine:
            print("Received a bad status line from Venstar ColorTouch")
            return False

        if not req.ok:
            print("Connection error logging into Venstar ColorTouch")
            return False

        return req

    def update_info(self):
        uri = "http://{0}/query/info".format(self.addr)
        ret = self._request(uri)

        if ret is False:
            return False

        self._info=r.json()
        return True

    def update_sensors(self):
        uri = "http://{0}/query/sensors".format(self.addr)
        ret = self._request(uri)

        if ret is False:
            return False
        self._sensors = r.json()

    def get_name(self):
        return self._info.["name"]

    def get_mode(self):
        return self._info["mode"]
