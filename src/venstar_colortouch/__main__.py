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


    return True

test()
