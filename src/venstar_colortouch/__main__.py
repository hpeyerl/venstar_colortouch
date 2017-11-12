from __future__ import print_function
import os,sys
import venstar_colortouch
import time

def usage():
    print("Usage: {0} <ip addr>".format(sys.argv[0]))

def test():
    if len(sys.argv) < 1:
        usage()
        return False

    a = sys.argv[1]
    print ("Testing with IP: {0}".format(a))

    ct = venstar_colortouch.VenstarColorTouch(a, timeout=5)

    if ct.login() is True:
        print("Login successful. API: {0} Type: {1}".format(ct._api_ver,ct._type))

    if ct.update_info() is True:
        print("Was able to get info:{0}".format(ct._info))
    else:
        print("Was not able to get info")

    print("Name is {n}\nFan is {f}\nHeat setpoint is {h}\nCool setpoint is {c}\n".format(n=ct.get_info("name"),f=ct.get_info("fan"),h=ct.get_info("heattemp"),c=ct.get_info("cooltemp")))

    if ct.update_sensors() is True:
        print("Was able to get sensors:{0}".format(ct._sensors))
    else:
        print("Was not able to get sensors")

    print("Indoor temp is {t} and humidity is {h}".format(t=ct.get_thermostat_sensor("temp"),h=ct.get_thermostat_sensor("hum")))

    print("Runtimes: {0}".format(ct.get_runtimes()))

    curh=ct.get_info("heattemp")
    curc=ct.get_info("cooltemp")
    ct.set_setpoints(60,90)
    ct.update_info()
    print("Heat setpoint is {h}\nCool setpoint is {c}\n".format(h=ct.get_info("heattemp"),c=ct.get_info("cooltemp")))
    ct.set_setpoints(curh,curc)
    ct.update_info()
    print("Heat setpoint is {h}\nCool setpoint is {c}\n".format(h=ct.get_info("heattemp"),c=ct.get_info("cooltemp")))

    return True

test()
