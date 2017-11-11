import json
import requests
import logging

MIN_API_VER=3

class VenstarColorTouch:
    def __init__(self, addr, timeout):
        self.addr = addr
        self.timeout = timeout
        self.status = {}
        self._api_ver = None
        self._type = None
        self._info = None
        self._sensors = None
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

    def _request(self, path):
        uri = "http://{addr}/{path}".format(addr=self.addr,path=path)
        try:
            req = requests.get(uri, timeout=self.timeout)
        except:
            print("Error requesting {uri} from Venstar ColorTouch".format(uri=uri))
            return False

        if not req.ok:
            print("Connection error logging into Venstar ColorTouch")
            return False

        print (req)
        return req

    def update_info(self):
        r = self._request("query/info")

        if r is False:
            return r

        print r.json()
        self._info=r.json()
        return True

    def update_sensors(self):
        ret = self._request("query/sensors")

        if ret is False:
            return False
        self._sensors = r.json()

    def get_name(self):
        return self._info["name"]

    def get_mode(self):
        return self._info["mode"]
