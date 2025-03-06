import pygame
from carla_kickstart.entities.vehicle import Vehicle, VehicleLight
from carla_kickstart.input import KeyboardState
from carla_kickstart.behaviors.base import ActorBehavior
import math
import numpy as np
import csv

from carla_kickstart.sensors.camera import CameraSensor

class AutopilotDrivingBehavior(ActorBehavior):
    """
    Use Carla's AutoPilot feature to control the vehicle
    """
    def attach(self, vehicle):
        super().attach(vehicle)
        self.vehicle.player.set_autopilot(True)

    def detach(self):
        super().detach()
        self.vehicle.player.set_autopilot(False)

    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):
        pass

class DrivingSafetyBehavior(ActorBehavior):

    def __init__(self):
        self.situation = "none"
        self.next_junction_has_stop_sign = False
        self.waited_at_stop_sign = False
        self.wait_before_continue = 0

    def on_situation_detected(self, name: str, intent: str):
        print(f"Situation: {name}, Current intent: {intent}")
        self.situation = name

        if intent == "TurnRight":
            self.vehicle.set_light(VehicleLight.RightBlinker, True)
        elif intent == "GoStraight":
            self.vehicle.set_light(VehicleLight.LeftBlinker, False)
            self.vehicle.set_light(VehicleLight.RightBlinker, False)
            self.next_junction_has_stop_sign = False

        self.waited_at_stop_sign = False

    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):

        if self.wait_before_continue > 0:
            self.wait_before_continue -= clock.get_time()
            if self.wait_before_continue < 0:
                self.wait_before_continue = 0

        cam: CameraSensor = self.vehicle.get_sensor("camera_front")
        if len(cam.detections) > 0:
            print(cam.detections)

        stop_signs = [x for x in cam.detections if x.class_name == "stop sign"]
        if len(stop_signs) > 0:
            self.next_junction_has_stop_sign = True

        if not self.waited_at_stop_sign:
            if self.situation == "BeforeJunction" and self.next_junction_has_stop_sign:
                # check for stop sign
                self.engine.brake()
                self.waited_at_stop_sign = True
                self.wait_before_continue = 2000
                return

        if self.situation == "CrossingZebra":
            persons = [x for x in cam.detections if x.class_name == "person"]
            if len(persons):
                self.engine.brake()
                return

        if self.wait_before_continue == 0:
            self.engine.accelerate()
