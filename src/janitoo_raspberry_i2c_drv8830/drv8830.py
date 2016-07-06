# -*- coding: utf-8 -*-
"""The Raspberry bmp thread

Server files using the http protocol

"""

__license__ = """
    This file is part of Janitoo.

    Janitoo is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Janitoo is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Janitoo. If not, see <http://www.gnu.org/licenses/>.

"""
__author__ = 'Sébastien GALLET aka bibi21000'
__email__ = 'bibi21000@gmail.com'
__copyright__ = "Copyright © 2013-2014-2015-2016 Sébastien GALLET aka bibi21000"

import logging
logger = logging.getLogger(__name__)

from janitoo.component import JNTComponent

##############################################################
#Check that we are in sync with the official command classes
#Must be implemented for non-regression
from janitoo.classes import COMMAND_DESC

COMMAND_MOTOR = 0x3100
COMMAND_SWITCH_MULTILEVEL = 0x0026
COMMAND_SWITCH_BINARY = 0x0025

assert(COMMAND_DESC[COMMAND_SWITCH_MULTILEVEL] == 'COMMAND_SWITCH_MULTILEVEL')
assert(COMMAND_DESC[COMMAND_SWITCH_BINARY] == 'COMMAND_SWITCH_BINARY')
assert(COMMAND_DESC[COMMAND_MOTOR] == 'COMMAND_MOTOR')
##############################################################

from janitoo_raspberry_i2c import OID

def make_minimoto(**kwargs):
    return MinimotoComponent(**kwargs)

class MinimotoComponent(JNTComponent):
    """ A motor component for gpio """

    def __init__(self, bus=None, addr=None, **kwargs):
        """
        """
        oid = kwargs.pop('oid', '%s.minimoto'%OID)
        name = kwargs.pop('name', "Motor")
        product_name = kwargs.pop('product_name', "Motor")
        product_type = kwargs.pop('product_type', "DC Motor")
        JNTComponent.__init__(self, oid=oid, bus=bus, addr=addr, name=name,
                product_name=product_name, product_type=product_type, **kwargs)
        logger.debug("[%s] - __init__ node uuid:%s", self.__class__.__name__, self.uuid)
        uuid="addr"
        self.values[uuid] = self.value_factory['config_array'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='The addresses of the motors separated by |',
            label='Adds',
            default='0x60|0x61',
        )
        uuid="drive"
        self.values[uuid] = self.value_factory['action_string'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='Drive the motor(s). Send a single value to apply to all motors or values separated with |',
            label='Drive',
            default='0',
            set_data_cb=self.set_drive,
            cmd_class=COMMAND_MOTOR,
        )
        uuid="stop"
        self.values[uuid] = self.value_factory['action_string'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='Stop the motor(s). Send a single value to apply to all motors or values separated with |',
            label='Stop',
            default='0',
            set_data_cb=self.set_stop,
            cmd_class=COMMAND_MOTOR,
        )
        uuid="brake"
        self.values[uuid] = self.value_factory['action_string'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='Brake the motor(s). Send a single value to apply to all motors or values separated with |',
            label='Brake',
            default='0',
            set_data_cb=self.set_brake,
            cmd_class=COMMAND_MOTOR,
        )

    def get_current_speed(self, node_uuid, index):
        """Get the current speed
        """
        current_state = self.values['actions'].get_data_index(index=index)
        if current_state == 'forward':
            return self.values['speed'].get_data_index(index=index)
        elif current_state == 'backward':
            return self.values['speed'].get_data_index(index=index) * -1
        else:
            return 0

    def set_drive(self, node_uuid, index, data):
        """Set the drive of the motor
        """
        self.values['speed'].set_data_index(index=index, data=data)
        try:
            m = self.values['num'].get_data_index(index=index)
            if m is not None:
                self._bus.i2c_acquire()
                try:
                    self._bus.drv8830_manager.getMotor(m).setSpeed(data)
                finally:
                    self._bus.i2c_release()
        except Exception:
            logger.exception('[%s] - Exception when setting speed')

    def set_stop(self, node_uuid, index, data):
        """Set the stop of the motor
        """
        self.values['speed'].set_data_index(index=index, data=data)
        try:
            m = self.values['num'].get_data_index(index=index)
            if m is not None:
                self._bus.i2c_acquire()
                try:
                    self._bus.drv8830_manager.getMotor(m).setSpeed(data)
                finally:
                    self._bus.i2c_release()
        except Exception:
            logger.exception('[%s] - Exception when setting speed')

    def set_brake(self, node_uuid, index, data):
        """Set the brake ot the motor
        """
        self.values['speed'].set_data_index(index=index, data=data)
        try:
            m = self.values['num'].get_data_index(index=index)
            if m is not None:
                self._bus.i2c_acquire()
                try:
                    self._bus.drv8830_manager.getMotor(m).setSpeed(data)
                finally:
                    self._bus.i2c_release()
        except Exception:
            logger.exception('[%s] - Exception when setting speed')


class Minimoto(object):

    # DRV8830 Registers
    __DRV8830_CONTROL           = 0x00
    __DRV8830_FAULT             = 0x01

    # Constructor
    def __init__(self, i2c, address, debug=False):
        """
        """
        if i2c is None:
            import Adafruit_GPIO.I2C as I2C
            i2c = I2C
        self._device = i2c.get_i2c_device( address, **kwargs )

    def drive(self, speed):
        """
        #Send the drive command over I2C to the DRV8830 chip. Bits 7:2 are the speed
        #setting; range is 0-63. Bits 1:0 are the mode setting:
        #- 00 = Standby/coast(HI-Z)
        #- 01 = Reverse
        #- 10 = Forward
        #- 11 = brake(H-H)
        """
        self._device.write8(self.__DRV8830_FAULT, 0x80) #Clear the fault status.
        speedval = abs(speed)
        if speedval > 63:            #Cap the value at 63
            speedval = 63
        speedval = speedval << 2  #Left shift to make room for bits 1:0
        if speed < 0:             #Set bits 1:0 based on sign of input
            speedval |= 0x01 #Reverse
        else:
            speedval |= 0x02 #Forward
            self._device.write8(self.__DRV8830_CONTROL, speedval) #control the moto
        return 1

    def stop(self):
        """
        #Coast to a stop by hi-z'ing the drivers.
        """
        self._device.write8(self.__DRV8830_CONTROL, 0x00) #Standby
        return 1

    def brake(self):
        """
        #Stop the motor by providing a heavy load on it.
        """
        self._device.write8(self.__DRV8830_CONTROL, 0x03)#brake
        return 1

    def get_fault(self):
        """
        #Return the fault status of the DRV8830 chip. Also clears any existing faults.
        """
        fault = self._device.readU8(self.__DRV8830_FAULT)
        self._device.write8(self.__DRV8830_FAULT, 0x80) #Clear the fault status.
        return fault
