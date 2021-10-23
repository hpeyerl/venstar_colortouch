from __future__ import print_function
import os,sys
import logging
import venstarcolortouch
import time

def usage():
    print("Usage: {0} <ip addr>".format(sys.argv[0]))

def test():
    # Initialize logging with level DEBUG
    logging.basicConfig(level=logging.DEBUG)

    if len(sys.argv) < 1:
        usage()
        return False

    a = sys.argv[1]

    if len(sys.argv) >= 3:
        proto = sys.argv[2]
    else:
        proto = 'http'

    if len(sys.argv) == 4:
        pin = sys.argv[3]
    else:
        pin = None

    if len(sys.argv) == 5:
        user = sys.argv[3]
        pwd = sys.argv[4]
    else:
        user = None
        pwd = None

    print ("Testing with IP: {0}".format(a))

    ct = venstarcolortouch.VenstarColorTouch(a, timeout=5, proto=proto, user=user, password=pwd, pin=pin)
    print("logging in...")
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

    print("Indoor temp is {t} and humidity is {h}".format(t=ct.get_indoor_temp(),h=ct.get_indoor_humidity()))
    print("Outdoor temp is {t}".format(t=ct.get_outdoor_temp()))

    sensors=ct.get_sensor_list()
    if sensors:
        print("\nAll sensors:")
        for sensor in sensors:
            print("{s} temp is {t}, humidity is {h}, battery is {b}, and type is {x}".format(s=sensor,t=ct.get_sensor(sensor,"temp"),h=ct.get_sensor(sensor,"hum"),b=ct.get_sensor(sensor,"battery"),x=ct.get_sensor(sensor,"type")))

    for type in ct.sensor_types:
        sensors=ct.get_sensor_list(type)
        if sensors:
            print("\n{x} sensors:".format(x=type))
            for sensor in sensors:
                print("{s} temp is {t}, humidity is {h}, battery is {b}, and type is {x}".format(s=sensor,t=ct.get_sensor(sensor,"temp"),h=ct.get_sensor(sensor,"hum"),b=ct.get_sensor(sensor,"battery"),x=ct.get_sensor(sensor,"type")))

    print()
    print("Runtimes: {0}".format(ct.get_runtimes()))

    curh=ct.get_info("heattemp")
    curc=ct.get_info("cooltemp")
    ct.set_setpoints(60,90)
    ct.update_info()
    print("Heat setpoint is {h}\nCool setpoint is {c}\n".format(h=ct.get_info("heattemp"),c=ct.get_info("cooltemp")))
    ct.set_setpoints(curh,curc)
    ct.update_info()
    print("Heat setpoint is {h}\nCool setpoint is {c}\n".format(h=ct.get_info("heattemp"),c=ct.get_info("cooltemp")))

    print("API Version is {v}".format(v=ct.get_api_ver()))
    print("Thermostat Type is {t}".format(t=ct.get_type()))

    return True

test()
