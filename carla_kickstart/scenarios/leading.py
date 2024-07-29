import carla
import pygame
from carla_kickstart.scenarios.single import SingleEgoVehicleScenario
from carla_kickstart.behaviors.base import ActorBehavior, NullBehavior
from carla_kickstart.behaviors.manual import ManualDrivingBehavior
from carla_kickstart.behaviors.autonomous import AutopilotDrivingBehavior
from carla_kickstart.vehicle import Vehicle
from carla_kickstart.input import KeyboardState
from carla_kickstart.sensors.collision import CollisionSensor
from carla_kickstart.sensors.inertials import IMUSensor
from carla_kickstart.sensors.lanes import LaneInvasionSensor
from carla_kickstart.sensors.location import GnssSensor
from carla_kickstart.sensors.radar import RadarSensor
from carla_kickstart.sensors.lidar import LidarSensor
from carla_kickstart.sensors.camera import CameraSensor
from carla_kickstart.config import available_car_models

class EgoVehicle(Vehicle):
    '''
    The main focus of this simulation
    '''
    def __init__(self, sim_id: str, world, model_id: str, spawn_point, behavior):
        Vehicle.__init__(self, world, model_id, spawn_point, behavior)
        # override actor name
        self.actor_role_name = "EGO_VEHICLE_" + sim_id
        self.player = None

    def setup_default_sensors(self):
        # Set up the sensors of the ego vehicle
        #self.attach_sensor("collision", CollisionSensor(self.player))
        #self.attach_sensor("lane", LaneInvasionSensor(self.player))
        self.attach_sensor("gnss", GnssSensor(self.player))
        self.attach_sensor("imu", IMUSensor(self.player))
        self.attach_sensor("radar", RadarSensor(self.player, draw_points=True))
        #self.attach_sensor("lidar", LidarSensor(self.player))
        #self.attach_sensor("camera_front", CameraSensor(self.player))

class LeadingVehicleScenario(SingleEgoVehicleScenario):
    """
    A scenario where a leading vehicle spawns in front of the ego vehicle
    """

    # the distance at which the leading vehicle should be spawned
    leading_spawn_distance = 10

    def __init__(self, ego_behavior: ActorBehavior, initial_spawn_point: int = 0, initial_model_index = 0):
        super().__init__(ego_behavior, initial_spawn_point, initial_model_index)
        self.leading_vehicle = None

    def attach(self, sim_root, sim_id: str):
        super().attach(sim_root, sim_id)

    def get_ego_vehicle(self) -> Vehicle:
         """
         Return the ego vehicle at its initial spawn point
         """
         return EgoVehicle(self.sim_id, self.world, available_car_models[self.model_index], self.get_ego_spawn_point(), self.ego_behavior)

    def restart(self):
        super().restart()
        ego_point = self.sim_root.ego.spawn_point
        distance_vector = ego_point.get_forward_vector() # is already a normalized vector
        distance_vector = distance_vector * self.leading_spawn_distance

        spawn_point = carla.Transform(ego_point.location + distance_vector, ego_point.rotation)

        if self.leading_vehicle is None:
            self.leading_vehicle = Vehicle(self.sim_root.world, 'vehicle.mercedes.coupe_2020', spawn_point, AutopilotDrivingBehavior())
            self.leading_vehicle.actor_role_name = "LEADING_VEHICLE_" + self.sim_id
            self.leading_vehicle.model_color_index = 3

        self.leading_vehicle.spawn_point = spawn_point
        self.leading_vehicle.restart()

    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):
        super().update(clock, keyboard_state)
        self.leading_vehicle.update(clock, keyboard_state)

