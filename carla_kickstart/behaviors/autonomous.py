import pygame
from carla_kickstart.vehicle import Vehicle
from carla_kickstart.input import KeyboardState
from carla_kickstart.behaviors.base import ActorBehavior

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

class AutonomousDrivingBehavior(ActorBehavior):
    def attach(self, vehicle):
        super().attach(vehicle)

    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):
        self.engine.accelerate()
