import pygame
import carla
from agents.navigation.basic_agent import BasicAgent
from agents.navigation.behavior_agent import BehaviorAgent
from carla_kickstart.basetypes import VehicleEngine
from carla_kickstart.behaviors.base import ActorBehavior
from carla_kickstart.entities.vehicle import VehicleLight
from carla_kickstart.input import KeyboardState

class DriveToLocationBehavior(ActorBehavior):

    def __init__(self):
        self.agent = None
        self.ended = False

    def attach(self, vehicle):
        ActorBehavior.attach(self, vehicle)
        vehicle.engine = OverrideEngineControl()

    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):
        if not self.ended:

            if self.agent is None:
                self.agent = BehaviorAgent(self.vehicle.player, 'cautious')
                # self.agent = BasicAgent(self.vehicle.player, target_speed=20)
                self.agent.set_target_speed(20)
                self.agent.set_destination(carla.Location(-1.24, 66.11, 0.0))
                self.agent.ignore_traffic_lights()
                self.agent.ignore_stop_signs()
                self.agent.ignore_vehicles()

            if self.agent.done():
                self.engine.brake()
                self.vehicle.set_light(VehicleLight.Brake, True)
                self.ended = True
            else:
                control = self.agent.run_step()
                control.manual_gear_shift = False
                self.vehicle.player.apply_control(control)

class OverrideEngineControl(VehicleEngine):
    """
    An engine model which ignores all commands
    as the vehicle is controlled autonomously
    """

    def accelerate(self, amount: float = 0.01):
        pass

    def brake(self, amount: float = 0.2):
        pass

    def emergency_brake(self):
        pass

    def idle(self):
        pass

    def steerLeft(self):
        pass

    def steerRight(self):
        pass

    def steer(self, amount: float):
        pass

    def is_reverse(self) -> bool:
        pass

    def toggle_reverse(self):
        pass

    def update(self, clock):
        pass
