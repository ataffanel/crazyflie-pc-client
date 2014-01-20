#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     ||          ____  _ __                           
#  +------+      / __ )(_) /_______________ _____  ___ 
#  | 0xBC |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
#  +------+    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
#   ||  ||    /_____/_/\__/\___/_/   \__,_/ /___/\___/
#
#  Copyright (C) 2011-2013 Bitcraze AB
#
#  Crazyflie Nano Quadcopter Client
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""
Driver for reading data from the py-sdl2 API. Used from Inpyt.py for reading input data.
"""

__author__ = 'Bitcraze AB'
__all__ = ['SdlReader']
import cfclient.sdl2 as sdl2
import logging

logger = logging.getLogger(__name__)

class SdlReader():
    """Used for reading data from input devices using the py-sdl2 API."""
    def __init__(self):
        self.inputMap = None
        sdl2.SDL_Init(sdl2.SDL_INIT_JOYSTICK | sdl2.SDL_INIT_NOPARACHUTE)
        self.j = None

    def start_input(self, deviceId, inputMap):
        """Initalize the reading and open the device with deviceId and set the mapping for axis/buttons using the
        inputMap"""
        logger.debug("start_input with deviceId {}".format(deviceId))
        self.data = {"roll":0.0, "pitch":0.0, "yaw":0.0, "thrust":0.0, "pitchcal":0.0, "rollcal":0.0, "estop": False, "exit":False, "althold":False}
        self.inputMap = inputMap
        if self.j:
            sdl2.joystick.SDL_JoystickClose(self.j)
        self.j = sdl2.joystick.SDL_JoystickOpen(deviceId)

    def read_input(self):
        """Read input from the selected device."""
        # We only want the pitch/roll cal to be "oneshot", don't
        # save this value.
        self.data["pitchcal"] = 0.0
        self.data["rollcal"]  = 0.0

        e = sdl2.events.SDL_Event()
        while sdl2.events.SDL_PollEvent(e) == 1:
          if e.type == sdl2.events.SDL_JOYAXISMOTION:
            index = "Input.AXIS-%d" % e.jaxis.axis
            try:
                if (self.inputMap[index]["type"] == "Input.AXIS"):
                    key = self.inputMap[index]["key"]
                    axisvalue = e.jaxis.value/32768.0
                    # All axis are in the range [-a,+a]
                    axisvalue = axisvalue * self.inputMap[index]["scale"]
                    # The value is now in the correct direction and in the range [-1,1]
                    self.data[key] = axisvalue
            except Exception:
                # Axis not mapped, ignore..
                pass          

          if e.type == sdl2.events.SDL_JOYBUTTONDOWN:
            index = "Input.BUTTON-%d" % e.jbutton.button
            try:
                if self.inputMap[index]["type"] == "Input.BUTTON":
                    key = self.inputMap[index]["key"]
                    if key == "estop":
                        self.data["estop"] = not self.data["estop"]
                    elif key == "exit":
                        self.data["exit"] = True
                    elif key == "althold":
                        self.data["althold"] = not self.data["althold"]                        
                    else:  # Generic cal for pitch/roll
                        self.data[key] = self.inputMap[index]["scale"]
            except Exception:
                # Button not mapped, ignore..
                pass
          
          if e.type == sdl2.events.SDL_JOYBUTTONUP:
            index = "Input.BUTTON-%d" % e.jbutton.button
            try:
                if self.inputMap[index]["type"] == "Input.BUTTON":
                    key = self.inputMap[index]["key"]
                    if key == "althold":
                        self.data["althold"] = False                     
            except Exception:
                # Button not mapped, ignore..
                pass            
            

        return self.data

    def enableRawReading(self, deviceId):
        """Enable reading of raw values (without mapping)"""
        logger.debug("Starting joystick {} for raw reading".format(deviceId))
        #if self.j:
        #    sdl2.joystick.SDL_JoystickClose(self.j)
        #    self.j = None
        self.j = sdl2.joystick.SDL_JoystickOpen(deviceId)

    def disableRawReading(self):
        """Disable raw reading"""
        logger.debug("Stopping joystick raw reading, closing joystick")
        #sdl2.joystick.SDL_JoystickClose(self.j)
        #self.j = None

    def readRawValues(self):
        """Read out the raw values from the device"""
        rawaxis = {}
        rawbutton = {}

        e = sdl2.events.SDL_Event()
        while sdl2.events.SDL_PollEvent(e) == 1:
            if e.type == sdl2.events.SDL_JOYBUTTONDOWN:
                rawbutton[e.jbutton.button] = 1
            if e.type == sdl2.events.SDL_JOYBUTTONDOWN:
                rawbutton[e.jbutton.button] = 0
            if e.type == sdl2.events.SDL_JOYBUTTONDOWN:
                rawaxis[e.jaxis.axis] = e.jaxis.value/32768.0

        return [rawaxis, rawbutton]

    def getAvailableDevices(self):
        """List all the available devices."""
        dev = []
        sdl2.SDL_QuitSubSystem(sdl2.SDL_INIT_JOYSTICK)
        sdl2.SDL_InitSubSystem(sdl2.SDL_INIT_JOYSTICK)
        sdl2.joystick.SDL_JoystickUpdate()
        nbrOfInputs = sdl2.joystick.SDL_NumJoysticks()
        for i in range(nbrOfInputs):
            dev.append({"id":i, "name" : sdl2.joystick.SDL_JoystickNameForIndex(i)})
        logger.debug("Scanning joystick" + dev.__str__())
        return dev

