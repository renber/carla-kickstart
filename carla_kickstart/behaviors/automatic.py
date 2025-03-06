import logging

from typing import Callable, List
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

logger = logging.getLogger(__name__)

class RouteWaypoint:

    def __init__(self, location, target_speed: float, state_name: str = "", intent: str = ""):
        self.location = location
        self.target_speed = target_speed
        self.state_name = state_name
        self.intent = intent

class FollowPredefinedRouteBehavior(ActorBehavior):

    def __init__(self, filename: str = None, waypoints: List[RouteWaypoint] = None, wait_at_waypoints: bool = False, driver_behavior = "normal", waypoint_reached_callback: Callable[[RouteWaypoint],None] = None):
        self.agent = None
        self.ended = False
        self.driver_behavior = driver_behavior
        if filename is not None and waypoints is not None:
            raise Exception("Cannot set filename and waypoints at the same time")

        if filename is not None:
            self.waypoints = self.__load_waypoints_from_file(filename)
        else:
            self.waypoints = self.__waypoints_from_list(waypoints)

        self.current_waypoint = None

        self.last_waypoint_distance = None

        self.wait_at_waypoints = wait_at_waypoints
        self.wait_for_continue = False
        self.on_waypoint_reached_callback = waypoint_reached_callback

    def __load_waypoints_from_file(self, filename: str) -> deque:
        lst = []

        with open(filename, "r") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                loc = carla.Location(x=float(row["X"]), y=float(row["Y"]), z=float(row["Z"]))
                speed = float(row["TargetSpeed"])
                state = row["State"]
                intent = row["Intent"]
                lst.append(RouteWaypoint(loc, speed, state, intent))

            return self.__waypoints_from_list(lst)

    def __waypoints_from_list(self, waypoints: List[RouteWaypoint]) -> deque:
        self.final_waypoint = waypoints[-1]

        waypoints.reverse() # reverse so that we can use as stack
        return deque(waypoints)

    def on_waypoint_reached(self, waypoint: RouteWaypoint):
        logger.debug(f"Reached {waypoint.state_name}")

        if self.on_waypoint_reached_callback is not None:
            self.on_waypoint_reached_callback(waypoint)

        if self.wait_at_waypoints:
            self.wait_for_continue = True

    def attach(self, vehicle):
        ActorBehavior.attach(self, vehicle)
        vehicle.engine = AgentEngineControl()

    def set_next_waypoint(self, waypoint: RouteWaypoint):
        self.current_waypoint = waypoint
        #self.agent.set_destination(self.current_waypoint.destination)
        self.agent.set_target_speed(self.current_waypoint.target_speed)
        self.last_waypoint_distance = None

        logger.debug(f"Approaching {waypoint.state_name} ({waypoint.location})")

    def has_reached_current_waypoint(self) -> bool:
        if self.current_waypoint is not None:
            dist = self.vehicle.location.distance(self.current_waypoint.location)
            self.last_waypoint_distance = dist

            if dist < 0.75:
                return True

        return False

    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):
        if not self.ended:

            if self.agent is None:
                self.agent = BehaviorAgent(self.vehicle.player, self.driver_behavior)
                self.agent.ignore_traffic_lights()
                self.agent.ignore_stop_signs()
                self.agent.ignore_vehicles()
                self.agent.set_destination(self.final_waypoint.location)
                self.set_next_waypoint(self.waypoints.pop())

            if self.agent.done():
                logger.info("DRIVING AGENT DONE")
                self.on_waypoint_reached(self.current_waypoint)
                self.ended = True
                self.current_waypoint = None
                self.vehicle.set_light(VehicleLight.Brake, True)
                return

            if self.has_reached_current_waypoint():
                self.on_waypoint_reached(self.current_waypoint)

                if len(self.waypoints) > 0:
                    self.set_next_waypoint(self.waypoints.pop())

            if self.engine.brake_requested:
                self.wait_for_continue = True

            # let the agent control the vehicle
            if self.wait_for_continue:
                self.wait_for_continue = self.engine.brake_requested

                if not self.wait_for_continue:
                    self.vehicle.set_light(VehicleLight.Brake, False)
                else:
                    self.vehicle.set_light(VehicleLight.Brake, True)
                    brake_control = carla.VehicleControl()
                    brake_control.brake = 5
                    self.vehicle.player.apply_control(brake_control)
            else:
                control = self.agent.run_step()
                control.manual_gear_shift = False
                self.vehicle.player.apply_control(control)

class AgentEngineControl(VehicleEngine):
    """
    An engine model which ignores all commands
    as the vehicle is controlled by an external agent
    However, brake/accelerate taken actions will be forwarded as hints to the driving agent
    """

    def __init__(self):
        VehicleEngine.__init__(self)

        self.brake_requested = False

    def accelerate(self, amount: float = 0.01):
        self.brake_requested = False

    def brake(self, amount: float = 0.2):
        self.brake_requested = True

    def emergency_brake(self):
        self.brake_requested = True

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
