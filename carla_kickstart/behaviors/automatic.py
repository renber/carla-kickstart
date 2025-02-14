import pygame
import carla
import csv
from agents.navigation.basic_agent import BasicAgent
from agents.navigation.behavior_agent import BehaviorAgent
from carla_kickstart.entities.base import VehicleEngine
from carla_kickstart.behaviors.base import ActorBehavior
from carla_kickstart.entities.vehicle import VehicleLight
from carla_kickstart.input import KeyboardState
from collections import deque

class RouteWaypoint:

    def __init__(self, destination, target_speed: float, state_name: str):
        self.destination = destination
        self.target_speed = target_speed
        self.state_name = state_name

class FollowPredefinedRouteBehavior(ActorBehavior):

    def __init__(self, filename: str):
        self.agent = None
        self.ended = False
        self.waypoints = self.__load_waypoints(filename)
        self.current_waypoint = None
        self.time_to_continue = 0
        self.wait_for_continue = False

    def __load_waypoints(self, filename: str) -> deque:
        lst = []

        with open(filename, "r") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                loc = carla.Location(x=float(row["X"]), y=float(row["Y"]), z=float(row["Z"]))
                speed = float(row["TargetSpeed"])
                state = row["State"]
                lst.append(RouteWaypoint(loc, speed, state))

        lst.reverse() # reverse so that we can use as stack
        return deque(lst)

    def __can_continue(self, keyboard_state: KeyboardState) -> bool:
        return keyboard_state.was_key_pressed(pygame.K_p)

    def on_state_entered(self, state_name: str):
        print(f"Current State = {state_name}")

    def on_state_ended(self, state_name: str):
        if state_name == "BeforeZebra":
            self.vehicle.set_light(VehicleLight.RightBlinker, True)
        elif state_name == "StopSign":
            self.vehicle.set_light(VehicleLight.RightBlinker, False)

    def attach(self, vehicle):
        ActorBehavior.attach(self, vehicle)
        vehicle.engine = OverrideEngineControl()

    def set_new_waypoint(self, waypoint: RouteWaypoint):
        self.current_waypoint = waypoint
        self.agent.set_destination(self.current_waypoint.destination)
        self.agent.set_target_speed(self.current_waypoint.target_speed)

        self.on_state_entered(waypoint.state_name)

    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):
        if not self.ended:

            if self.agent is None:
                self.agent = BehaviorAgent(self.vehicle.player, 'cautious')
                self.agent.ignore_traffic_lights()
                self.agent.ignore_stop_signs()
                self.agent.ignore_vehicles()
                self.set_new_waypoint(self.waypoints.pop())

            if self.wait_for_continue:
                if self.__can_continue(keyboard_state):
                    self.wait_for_continue = False
                    self.set_new_waypoint(self.waypoints.pop())
                    self.vehicle.set_light(VehicleLight.Brake, False)
                else:
                    return # keep waiting

            if self.agent.done():
                self.on_state_ended(self.current_waypoint.state_name)

                if len(self.waypoints) == 0:
                    self.current_waypoint = None
                    self.vehicle.set_light(VehicleLight.Brake, True)
                    self.ended = True

                    return # route finished
                else:
                    if self.__can_continue(keyboard_state):
                        self.set_new_waypoint(self.waypoints.pop())
                    else:
                        self.current_waypoint = None
                        self.wait_for_continue = True
                        self.vehicle.set_light(VehicleLight.Brake, True)

            # let the agent control the vehicle
            if self.current_waypoint is not None:
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
