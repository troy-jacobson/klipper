# Exclude moves toward and inside set regions
#
# Copyright (C) 2019  Eric Callahan <arksine.code@gmail.com>
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import math
import logging
import json
from datetime import datetime

class ExcludeRegion:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        # Temporary workaround to get skew_correction to register
        # its "klippy:ready" event handler before Exclude Region.  Exclude
        # Region needs to be the highest priority transform, thus it must be
        # the last module that calls set_move_transform()
        if config.has_section('skew_correction'):
            self.printer.try_load_module(config, 'skew_correction')
        # Now ExcludeRegion can register its own event handler
        self.printer.register_event_handler("klippy:ready",
                                            self._handle_ready)
        self.printer.register_event_handler("sdcard:reset_file",
                                            self._handle_reset_file)
        self.objects = {}
        self.excluded_objects = []
        self.current_object = ""
        self.in_excluded_region = False
        self.last_position = [0., 0., 0., 0.]
        self.last_position_extruded = [0., 0., 0., 0.]
        self.last_position_excluded = [0., 0., 0., 0.]
        self.gcode.register_command(
            'START_CURRENT_OBJECT', self.cmd_START_CURRENT_OBJECT,
            desc=self.cmd_START_CURRENT_OBJECT_help)
        self.gcode.register_command(
            'END_CURRENT_OBJECT', self.cmd_END_CURRENT_OBJECT,
            desc=self.cmd_END_CURRENT_OBJECT_help)
        self.gcode.register_command(
            'EXCLUDE_OBJECT', self.cmd_EXCLUDE_OBJECT,
            desc=self.cmd_EXCLUDE_OBJECT_help)
        self.gcode.register_command(
            'REMOVE_ALL_EXCLUDED', self.cmd_REMOVE_ALL_EXCLUDED,
            desc=self.cmd_REMOVE_ALL_EXCLUDED_help)
        self.gcode.register_command(
            'DEFINE_OBJECT', self.cmd_DEFINE_OBJECT,
            desc=self.cmd_DEFINE_OBJECT_help)
        self.gcode.register_command(
            'LIST_OBJECTS', self.cmd_LIST_OBJECTS,
            desc=self.cmd_LIST_OBJECTS_help)
        self.gcode.register_command(
            'LIST_EXCLUDED_OBJECTS', self.cmd_LIST_EXCLUDED_OBJECTS,
            desc=self.cmd_LIST_EXCLUDED_OBJECTS_help)
        # debugging
        self.current_region = None
    def _handle_ready(self):
        gcode_move = self.printer.lookup_object('gcode_move')
        self.next_transform = gcode_move.set_move_transform(self, force=True)
    def get_position(self):
        self.last_position[:] = self.next_transform.get_position()
        self.last_delta = [0., 0., 0., 0.]
        return list(self.last_position)

    def _normal_move(self, newpos, speed):
        self.last_position_extruded[:] = newpos
        self.last_position[:] = newpos
        self.next_transform.move(newpos, speed)

    def _ignore_move(self, newpos, speed):
        self.last_position_excluded[:] = newpos
        self.last_position[:] = newpos
        return

    def _move_into_excluded_region(self, newpos, speed):
        logging.info("Moving to excluded object: " + self.current_object)
        self.in_excluded_region = True
        self.last_position_excluded[:] = newpos
        self.last_position[:] = newpos

    def _move_from_excluded_region(self, newpos, speed):
        logging.info("Moving to included object: " + self.current_object)
        logging.info("last position: " + " ".join(str(x) for x in self.last_position))
        logging.info("last extruded position: " + " ".join(str(x) for x in self.last_position_extruded))
        logging.info("last excluded position: " + " ".join(str(x) for x in self.last_position_excluded))
        logging.info("New position: " + " ".join(str(x) for x in newpos))
        if self.last_position[0] == newpos[0] and self.last_position[1] == newpos[1]:
            # If the X,Y position didn't change for this transitional move, assume that this move
            # should happen at the last extruded location
            newpos[0] = self.last_position_extruded[0]
            newpos[1] = self.last_position_extruded[1]
        newpos[3] = newpos[3] - self.last_position_excluded[3] + self.last_position_extruded[3]
        logging.info("Modified position: " + " ".join(str(x) for x in newpos))
        self.last_position[:] = newpos
        self.last_position_extruded[:] = newpos
        self.next_transform.move(newpos, speed)
        self.in_excluded_region = False

    def _test_in_excluded_region(self):
        # Inside cancelled object
        if self.current_object in self.excluded_objects:
            return True

    def get_status(self, eventtime=None):
        status = {
            "objects": self.objects.values(),
            "excluded_objects": list(self.excluded_objects),
            "current_object": self.current_object
        }
        return status

    def move(self, newpos, speed):
        move_in_excluded_region = self._test_in_excluded_region()

        if move_in_excluded_region:
            if self.in_excluded_region:
                self._ignore_move(newpos, speed)
            else:
                self._move_into_excluded_region(newpos, speed)
        else:
            if self.in_excluded_region:
                self._move_from_excluded_region(newpos, speed)
            else:
                self._normal_move(newpos, speed)

    cmd_START_CURRENT_OBJECT_help = "Marks the beginning the current object as labeled"
    def cmd_START_CURRENT_OBJECT(self, params):
        name = params.get_command_parameters()['NAME'].upper()
        if name not in self.objects:
            obj = {
                "name": name
            }
            self.objects[name] = obj
        self.current_object = name
    cmd_END_CURRENT_OBJECT_help = "Markes the end the current object"
    def cmd_END_CURRENT_OBJECT(self, params):
        self.current_object = ""
    cmd_EXCLUDE_OBJECT_help = "Cancel moves inside a specified objects"
    def cmd_EXCLUDE_OBJECT(self, params):
        name = params.get_command_parameters()['NAME'].upper()
        if name not in self.excluded_objects:
            self.excluded_objects.append(name)
    cmd_REMOVE_ALL_EXCLUDED_help = "Removes all excluded objects and regions"
    def cmd_REMOVE_ALL_EXCLUDED(self, params):
        logging.info("cmd_remove_all_excluded")
        self._handle_reset_file()
    cmd_LIST_OBJECTS_help = "Lists the known objects"
    def cmd_LIST_OBJECTS(self, gcmd):
        object_list = " ".join (str(x) for x in self.objects.values())
        gcmd.respond_info(object_list)
    cmd_LIST_EXCLUDED_OBJECTS_help = "Lists the excluded objects"
    def cmd_LIST_EXCLUDED_OBJECTS(self, gcmd):
        object_list = " ".join (str(x) for x in self.excluded_objects)
        gcmd.respond_info(object_list)
    cmd_DEFINE_OBJECT_help = "Provides a summary of an object"
    def cmd_DEFINE_OBJECT(self, params):
        name = params.get_command_parameters()['NAME'].upper()
        center = params.get_command_parameters()['CENTER'].upper()
        outline = params.get_command_parameters()['POLYGON'].upper()

        obj = {
            "name": name,
            "center": [float(coord) for coord in center.split(',')],
            "outline": json.loads(outline)
        }

        if name not in self.objects:
            self.objects[name] = obj

    def _handle_reset_file(self):
        logging.info("handle_reset_file")
        self.objects = {}
        self.excluded_objects = []

def load_config(config):
    return ExcludeRegion(config)
