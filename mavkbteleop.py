#!/usr/bin/env python
# vim:set ts=4 sw=4 et:
#
# Copyright 2014 Vladimir Ermakov.
#
# This file is part of the mavros package and subject to the license terms
# in the top-level LICENSE file of the mavros repository.
# https://github.com/mavlink/mavros/tree/master/LICENSE.md

from __future__ import print_function

import argparse

import rospy
import sys, select, termios, tty
from tf.transformations import quaternion_from_euler
from sensor_msgs.msg import Joy
from std_msgs.msg import Header, Float64
from geometry_msgs.msg import PoseStamped, TwistStamped, Vector3, Quaternion, Point
from mavros_msgs.msg import OverrideRCIn
from mavros_msgs.srv import CommandBool
from mavros_msgs.srv import CommandTOL
from mavros_msgs.srv import SetMode

def getKey():
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''

    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def arm(args, state):
    #rospy.wait_for_service('/cmd/arming')
    try:
        arming_cl = rospy.ServiceProxy(args.mavros_ns + "/cmd/arming", CommandBool)
        ret = arming_cl(value=state)
    except rospy.ServiceException as ex:
        fault(ex)

    if not ret.success:
        rospy.loginfo("ARM Request failed.")
    else:
        rospy.loginfo("ARM Request success.")

def takeoff(args):
    #rospy.wait_for_service('/cmd/takeoff')
    try:
        takeoff_cl = rospy.ServiceProxy(args.mavros_ns + "/cmd/takeoff", CommandTOL)

        ret = takeoff_cl(min_pitch=0, yaw=0, latitude=47.397751, longitude=8.545607, altitude=10)
    except rospy.ServiceException as ex:
        fault(ex)

    if not ret.success:
        rospy.loginfo("TAKEOFF Request failed.")
    else:
        rospy.loginfo("TAKEOFF Request success.")

def land(args):
    #rospy.wait_for_service('/cmd/takeoff')
    try:
        takeoff_cl = rospy.ServiceProxy(args.mavros_ns + "/cmd/land", CommandTOL)

        ret = takeoff_cl(min_pitch=0, yaw=0, latitude=47.397751, longitude=8.545607, altitude=0)
    except rospy.ServiceException as ex:
        fault(ex)

    if not ret.success:
        rospy.loginfo("TAKEOFF Request failed.")
    else:
        rospy.loginfo("TAKEOFF Request success.")

def set_mode(args, mode):
    try:
        setmode_cl = rospy.ServiceProxy(args.mavros_ns + "/set_mode", SetMode)

        #ret = setmode_cl(base_mode=0, custom_mode="MANUAL")
        ret = setmode_cl(base_mode= 2, custom_mode=mode)
    except rospy.ServiceException as ex:
        fault(ex)

   # if not ret.success:
    #    rospy.loginfo("SET MODE Request failed.")
   # else:
    #    rospy.loginfo("SET MODE Request success.")


def rc_override_control(args):

    rospy.init_node("mavkbteleop")
    rospy.loginfo("MAV-Teleop: RC Override control type.")


    override_pub = rospy.Publisher(args.mavros_ns + "/rc/override", OverrideRCIn, queue_size=10)

    throttle_ch = 1500

    #rate = rospy.Rate(10)

    while(1):
        roll = 1500
        pitch = 1500
        key = getKey()
        #rospy.loginfo("Key: %s", key)
        if key == '1':
            arm(args, True)
        elif key == '2':
            arm(args, False)
        elif key == '3':
	        takeoff(args)
        elif key == '4':
	        land(args)
        elif key == 'h':
            #set_mode(args, "MANUAL")
            set_mode(args, "STABILIZED")
        elif key == '0':
            set_mode(args, "OFFBOARD")
        elif key == 'r': #UP
	        throttle_ch+=10
    	elif key == 'f': #FIX
	        throttle_ch=1500
        elif key == 'v': #DOWN
	        throttle_ch-=10 
        elif key == 'j': #LEFT
	        roll=1800   
     	elif key == 'l': #RIGHT
	        roll=1200   
     	elif key == 'i': #FORWARD
	        pitch=1800 
        elif key == 'k': #BACKWARD
	        pitch=1200 
        if (key == '\x03'):
            break

        rc = OverrideRCIn()
        rc.channels[0] = roll
        rc.channels[1] = pitch
        rc.channels[2] = throttle_ch
        rc.channels[3] = 1500 #yaw
        rc.channels[4] = 1000
        rc.channels[5] = 1000
        rc.channels[6] = 1000
        rc.channels[7] = 1000

        rospy.loginfo("Channels: %d %d %d %d", rc.channels[0], rc.channels[1],rc.channels[2] , rc.channels[3])

        override_pub.publish(rc)
       # rate.sleep()


def main():
    parser = argparse.ArgumentParser(description="Teleoperation script for Copter-UAV")
    parser.add_argument('-n', '--mavros-ns', help="ROS node namespace", default="/mavros")
    parser.add_argument('-v', '--verbose', action='store_true', help="verbose output")
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('-rc', '--rc-override', action='store_true', help="use rc override control type")
    mode_group.add_argument('-att', '--sp-attitude', action='store_true', help="use attitude setpoint control type")
    mode_group.add_argument('-vel', '--sp-velocity', action='store_true', help="use velocity setpoint control type")
    mode_group.add_argument('-pos', '--sp-position', action='store_true', help="use position setpoint control type")

    args = parser.parse_args(rospy.myargv(argv=sys.argv)[1:])

    if args.rc_override:
        rc_override_control(args)


if __name__ == '__main__':
    settings = termios.tcgetattr(sys.stdin)
    main()
