import pygame
from carla_kickstart.input import KeyboardState
from abc import ABC, abstractmethod
from carla_kickstart.basetypes import VehicleEngine

class ActorBehavior(ABC):

    def __init__(self):
        pass

    def attach(self, vehicle):
        self.vehicle = vehicle

    @property
    def engine(self) -> VehicleEngine:
        return self.vehicle.engine

    def detach(self):
        pass

    @abstractmethod
    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):
        # Implement behavior in a base class here
        pass

class NullBehavior(ActorBehavior):
    """
    A behavior which does nothing
    """
    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):
        pass

class CompoundBehavior(ActorBehavior):
    """
    Allows to combine multiple behaviors
    """

    def __init__(self, *behaviors):
        self.behaviors = behaviors

    def attach(self, vehicle):
        for b in self.behaviors:
            b.attach(vehicle)

    @property
    def engine(self):
        return None

    def detach(self):
        for b in self.behaviors:
            b.detach()

    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):
        for b in self.behaviors:
            b.update(clock, keyboard_state)