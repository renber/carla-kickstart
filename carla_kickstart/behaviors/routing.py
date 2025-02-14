

import pygame
import carla
from agents.navigation.basic_agent import BasicAgent
from agents.navigation.behavior_agent import BehaviorAgent
from carla_kickstart.basetypes import VehicleEngine
from carla_kickstart.behaviors.base import ActorBehavior
from carla_kickstart.entities.vehicle import VehicleLight
from carla_kickstart.input import KeyboardState


class RouteRecorderBehavior(ActorBehavior):

    RECORD_EVERY_MS = 500

    def __init__(self, filename: str, record_interval_ms: int = 0):
        self.f = open(filename, "w")
        self.f.write("Time;X;Y;Z\n")
        self.f.flush()

        self.is_recording = False
        self.time_since_last_recording = 0
        self.record_interval_ms = record_interval_ms
        self.total_time = 0

    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):

        do_record = False
        if self.record_interval_ms <= 0:
            # record the current position if L was pressed
            do_record = keyboard_state.was_key_pressed(pygame.K_l)
        else:
            # recording based on time

            # start recording as soon as the car begins moving
            if not self.is_recording:
                if self.engine.is_accelerating():
                    self.is_recording = True
                    self.time_since_last_recording = 2000
                else:
                    return

            self.total_time += clock.get_time()
            self.time_since_last_recording += clock.get_time()
            do_record = self.time_since_last_recording >= self.RECORD_EVERY_MS

        if do_record:
            loc = self.vehicle.location
            line = f"{self.total_time};{loc.x};{loc.y};{loc.z}"
            self.f.write(f"{line}\n")
            self.f.flush()
            print(line)
            self.time_since_last_recording = 0
