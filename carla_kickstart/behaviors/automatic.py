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

    def __init__(self, location, target_speed: float, state_name: str):
        self.location = location
        self.target_speed = target_speed
        self.state_name = state_name

class FollowPredefinedRouteBehavior(ActorBehavior):

    def __init__(self, filename: str):
        self.agent = None
        self.ended = False
        self.waypoints = self.__load_waypoints(filename)
        self.current_waypoint = None

        self.last_waypoint_distance = None

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

        self.final_waypoint = lst[-1]

        lst.reverse() # reverse so that we can use as stack
        return deque(lst)

    def on_waypoint_reached(self, waypoint: RouteWaypoint):
        print(f"Reached {waypoint.state_name}")
        if waypoint.state_name in ("BeforeZebra", "BeforeJunction"):
            self.vehicle.set_light(VehicleLight.RightBlinker, True)
        elif waypoint.state_name in ("AfterZebra", "AfterJunction"):
            self.vehicle.set_light(VehicleLight.RightBlinker, False)

    def attach(self, vehicle):
        ActorBehavior.attach(self, vehicle)
        vehicle.engine = AgentEngineControl()

    def set_next_waypoint(self, waypoint: RouteWaypoint):
        self.current_waypoint = waypoint
        #self.agent.set_destination(self.current_waypoint.destination)
        self.agent.set_target_speed(self.current_waypoint.target_speed)
        self.last_waypoint_distance = None

        print(f"Approaching {waypoint.state_name} ({waypoint.location})")

    def has_reached_current_waypoint(self) -> bool:
        if self.current_waypoint is not None:
            dist = self.vehicle.location.distance(self.current_waypoint.location)
            last_dist = self.last_waypoint_distance
            self.last_waypoint_distance = dist

            if dist < 1:
                return True

            # we have passed the waypoint without actually reaching it
            #if last_dist is not None and dist > last_dist:
            #    return True

        return False

    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):
        if not self.ended:

            if self.agent is None:
                self.agent = BehaviorAgent(self.vehicle.player, 'cautious')
                self.agent.ignore_traffic_lights()
                self.agent.ignore_stop_signs()
                self.agent.ignore_vehicles()
                self.agent.set_destination(self.final_waypoint.location)
                self.set_next_waypoint(self.waypoints.pop())

            if self.agent.done():
                print("AGENT DONE")
                self.on_waypoint_reached(self.current_waypoint)
                self.ended = True
                self.current_waypoint = None
                self.vehicle.set_light(VehicleLight.Brake, True)
                return

            if self.has_reached_current_waypoint():
                self.on_waypoint_reached(self.current_waypoint)

                if len(self.waypoints) > 0:
                    self.set_next_waypoint(self.waypoints.pop())

            # let the agent control the vehicle
            control = self.agent.run_step()
            control.manual_gear_shift = False
            self.vehicle.player.apply_control(control)

class AgentEngineControl(VehicleEngine):
    """
    An engine model which ignores all commands
    as the vehicle is controlled by an external agent
    However, taken actions will be forwarded as hints to the agent
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
