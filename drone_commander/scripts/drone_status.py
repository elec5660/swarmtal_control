#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import print_function
import argparse
import rospy
from swarmtal_msgs.msg import drone_onboard_command
import sys
import math
import numpy as np
import rosgraph
import os, time
from termcolor import colored
from sensor_msgs.msg import BatteryState
from geometry_msgs.msg import Point, Vector3
from nav_msgs.msg import Odometry

def printBatteryLevel (battery_level, total=100, prefix ='', suffix ='', length = 100, fill ='█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:4.1f}%").format(100 * (battery_level / float(total)))
    filledLength = int(length * battery_level // total)
    bar = "|" + fill * filledLength + '-' * (length - filledLength) +"|"
    bar_color = "blue"
    if battery_level < 30:
        bar_color = "red"
    elif battery_level < 70:
        bar_color = "yellow"
    elif battery_level < 95:
        bar_color = "green"

    print('\r%s %s %s %s' % (prefix, colored(bar, bar_color), colored(percent, bar_color), suffix), end = '\r')
    sys.stdout.flush()


battery_votage = 0.0
vo_position = Vector3()
vo_avail = False
last_vo_time = 0

def on_battery_status(bat_msg):
    global battery_votage
    battery_votage = bat_msg.voltage


def on_vo_msg(vo_msg):
    global vo_avail, vo_position, last_vo_time
    vo_avail = True
    vo_position = vo_msg.pose.pose.position
    last_vo_time = rospy.get_time()

def battery_to_percent(bat):
    if bat > 14.8:
        return (bat - 14.8)/(16.8-14.8)*0.5+0.5
    if 0<bat < 14.8:
        return (bat-14.4)/(14.8-14.4)*0.5
    return 0

def work(vo_topic="/uwb_vicon_odom"):
    global vo_avail, vo_position, last_vo_time, battery_votage

    rospy.init_node("drone_status")
    s_bat = rospy.Subscriber("/dji_sdk_1/dji_sdk/battery_state", BatteryState, on_battery_status)
    s_vo = rospy.Subscriber(vo_topic, Odometry, on_vo_msg)
    #Wait for dji_sdk
    rospy.loginfo("Wait for dji sdk.....")
    # rospy.wait_for_service("/dji_sdk_1/dji_sdk/set_hardsyc")
    rospy.loginfo("DJI SDK started")
    r = rospy.Rate(10)
    while not rospy.is_shutdown() and rosgraph.is_master_online():
        prefix = "[{:7.3f}s]".format(rospy.get_time() % 1000)
        if vo_avail:
            vo_color = "green"
        else:
            vo_color = "red"

        vo_str = " VO {} :[{:5.3f}, {:5.3f}, {:5.3f}]".format(vo_avail, vo_position.x, vo_position.y, vo_position.z)
        prefix = prefix + colored(vo_str, vo_color) + " BAT:"
        bat_l = battery_to_percent(battery_votage) * 100
        suffix = ":{:4.2f}V".format(battery_votage)
        printBatteryLevel(bat_l, 100, prefix, suffix, length=10)
        r.sleep()

        if rospy.get_time() - last_vo_time > 0.1:
            vo_avail = False
    print()

if __name__ == "__main__":
    while not rospy.is_shutdown():
        if rosgraph.is_master_online():
            if len(sys.argv) > 1:
                vo_topic = sys.argv[1]
            else:
                vo_topic = "/uwb_vicon_odom"
            work(vo_topic)
        else:
            print("[DRONE_STATUS][{}] Wait For rosmaster".format(time.time()))
            time.sleep(1.0)
