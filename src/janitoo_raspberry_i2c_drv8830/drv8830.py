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
        uuid="speed"
        self.values[uuid] = self.value_factory['config_byte'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='The speed of the motor. A byte from 0 to 255',
            label='Speed',
            default=0,
            set_data_cb=self.set_speed,
        )
        uuid="max_speed"
        self.values[uuid] = self.value_factory['config_byte'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help="The max speed supported by the motor. Some motor doesn't seems support 100% PWM. A byte from 0 to 255",
            label='Speed',
            default=255,
        )
        uuid="num"
        self.values[uuid] = self.value_factory['config_byte'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='The number of the motor on the Hat board. A byte from 1 to 4',
            label='Num.',
        )
        uuid="actions"
        self.values[uuid] = self.value_factory['action_list'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='The action on the DC motor',
            label='Actions',
            list_items=['forward', 'backward', 'release'],
            default='release',
            set_data_cb=self.set_action,
            is_writeonly = True,
            cmd_class=COMMAND_MOTOR,
            genre=0x01,
        )
        uuid="current_speed"
        self.values[uuid] = self.value_factory['sensor_integer'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='The current speed of the motor. An integer from -255 to 255',
            label='CSpeed',
            get_data_cb=self.get_current_speed,
        )
        poll_value = self.values[uuid].create_poll_value(default=300)
        self.values[poll_value.uuid] = poll_value

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

    def set_speed(self, node_uuid, index, data):
        """Set the speed ot the motor
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

    def set_action(self, node_uuid, index, data):
        """Act on the motor
        """
        params = {}
        if data == "forward":
            try:
                m = self.values['num'].get_data_index(index=index)
                if m is not None:
                    self._bus.i2c_acquire()
                    try:
                        self._bus.drv8830_manager.getMotor(m).run(Adafruit_MotorHAT.FORWARD)
                    finally:
                        self._bus.i2c_release()
            except Exception:
                logger.exception('[%s] - Exception when running forward')
        elif data == "backward":
            try:
                m = self.values['num'].get_data_index(index=index)
                if m is not None:
                    self._bus.i2c_acquire()
                    try:
                        self._bus.drv8830_manager.getMotor(m).run(Adafruit_MotorHAT.BACKWARD)
                    finally:
                        self._bus.i2c_release()
            except Exception:
                logger.exception('[%s] - Exception when running backward')
        elif data == "release":
            m = self.values['num'].get_data_index(index=index)
            if m is not None:
                try:
                    self._bus.i2c_acquire()
                    try:
                        self._bus.drv8830_manager.getMotor(m).run(Adafruit_MotorHAT.RELEASE)
                    finally:
                        self._bus.i2c_release()
                except Exception:
                    logger.exception('[%s] - Exception when releasing one motor %s', self.__class__.__name__, m)