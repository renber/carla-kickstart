import pygame
from carla_kickstart.vehicle import Vehicle
from carla_kickstart.input import KeyboardState
from carla_kickstart.behaviors.base import ActorBehavior
from carla_kickstart.sensors.radar import RadarPoint
from typing import List

class CruiseControl(ActorBehavior):

    target_speed = 50

    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):
        pass

class EmergencyBrake(ActorBehavior):
    
    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):
        self.engine.emergency_brake()        