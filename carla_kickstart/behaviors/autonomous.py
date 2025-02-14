import pygame
from carla_kickstart.entities.vehicle import Vehicle
from carla_kickstart.input import KeyboardState
from carla_kickstart.behaviors.base import ActorBehavior
import math
import numpy as np
import csv

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

# based on https://medium.com/@chardorn/creating-carla-waypoints-9d2cc5c6a656
class RouteFollowBehavior(ActorBehavior):

    def __init__(self, filename: str):
        self.waypoints = self.__load_waypoints(filename)
        self.current_waypoint = None

    def attach(self, vehicle):
        ActorBehavior.attach(self, vehicle)

        physics_control = vehicle.player.get_physics_control()
        self.max_steer = physics_control.wheels[0].max_steer_angle
        rear_axle_center = (physics_control.wheels[2].position + physics_control.wheels[3].position)/200
        offset = rear_axle_center - vehicle.location
        self.wheelbase = np.linalg.norm([offset.x, offset.y, offset.z])

    def __load_waypoints(self, filename: str) -> list:
        lst = []

        with open(filename, "r") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                loc = carla.Location(x=float(row["X"]), y=float(row["Y"]), z=float(row["Z"]))
                lst.append(loc)

        return lst

    def get_next_waypoint(self):
        vehicle_location = self.vehicle.location
        min_distance = 1000
        next_waypoint = None

        for waypoint_location in self.waypoints:
            #Only check waypoints that are in the front of the vehicle (if x is negative, then the waypoint is to the rear)
            #TODO: Check if this applies for all maps
            if (waypoint_location - vehicle_location).x > 0:

                #Find the waypoint closest to the vehicle, but once vehicle is close to upcoming waypoint, search for next one
                if vehicle_location.distance(waypoint_location) < min_distance and vehicle_location.distance(waypoint_location) > 5:
                    min_distance = vehicle_location.distance(waypoint_location)
                    next_waypoint = waypoint_location

        return next_waypoint

    def control_pure_pursuit(self, vehicle_tr, waypoint, max_steer, wheelbase):
        # TODO: convert vehicle transform to rear axle transform
        wp_loc_rel = self.relative_location(vehicle_tr, waypoint) + carla.Vector3D(wheelbase, 0, 0)
        wp_ar = [wp_loc_rel.x, wp_loc_rel.y]
        d2 = wp_ar[0]**2 + wp_ar[1]**2
        steer_rad = math.atan(2 * wheelbase * wp_loc_rel.y / d2)
        steer_deg = math.degrees(steer_rad)
        steer_deg = np.clip(steer_deg, -max_steer, max_steer)
        return steer_deg / max_steer

    def relative_location(self, frame, location):
        origin = frame.location
        forward = frame.get_forward_vector()
        right = frame.get_right_vector()
        up = frame.get_up_vector()
        disp = location - origin
        x = np.dot([disp.x, disp.y, disp.z], [forward.x, forward.y, forward.z])
        y = np.dot([disp.x, disp.y, disp.z], [right.x, right.y, right.z])
        z = np.dot([disp.x, disp.y, disp.z], [up.x, up.y, up.z])
        return carla.Vector3D(x, y, z)

    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):
        new_waypoint = self.get_next_waypoint()
        if new_waypoint != self.current_waypoint:
            self.current_waypoint = new_waypoint
            print(f"Next Waypoint: {new_waypoint}")

        # reached end
        if self.current_waypoint is None:
            self.engine.brake()
            return

        steer = self.control_pure_pursuit(self.vehicle.player.get_transform(), self.current_waypoint, self.max_steer, self.wheelbase)
        print(steer)
        # control = carla.VehicleControl(throttle, steer)
        if self.vehicle.speed < 30:
            self.engine.accelerate()
        else:
            self.engine.idle()

        self.engine.steer(steer)