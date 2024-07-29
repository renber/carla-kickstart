import pygame
from carla_kickstart.scenarios.base import SimulationScenario
from carla_kickstart.behaviors.base import ActorBehavior
from carla_kickstart.behaviors.manual import ManualDrivingBehavior, ManualWalkBehavior
from carla_kickstart.entities.vehicle import Vehicle
from carla_kickstart.entities.person import Person
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
        self.attach_sensor("gnss", GnssSensor(self.player))
        self.attach_sensor("imu", IMUSensor(self.player))
        #self.attach_sensor("radar", RadarSensor(self.player))
        #self.attach_sensor("camera_front", CameraSensor(self.player, False))
        #self.attach_sensor("lidar", LidarSensor(self.player))        
        #self.attach_sensor("collision", CollisionSensor(self.player))
        #self.attach_sensor("lane", LaneInvasionSensor(self.player))

class SingleEgoVehicleScenario(SimulationScenario):
    """
    Spawns a single ego vehicle with the given behavior
    """

    def __init__(self, ego_behavior: ActorBehavior, initial_spawn_point: int = 0, initial_model_index = 0):
        self.spawn_point_index = initial_spawn_point
        self.model_index = initial_model_index
        self.ego_behavior = ego_behavior

    def attach(self, sim_root, sim_id: str):
        super().attach(sim_root, sim_id)

        if not self.map.get_spawn_points():
            raise(Exception('There are no spawn points available in your map/town. Please add some Vehicle Spawn Point to your UE4 scene.'))
        self.spawn_points_count = len(self.map.get_spawn_points())

    def get_ego_spawn_point(self):
        spawn_points = self.map.get_spawn_points()
        spawn_point = spawn_points[self.spawn_point_index]
        return spawn_point

    def get_ego_vehicle(self) -> Vehicle:
         """
         Return the ego vehicle at its initial spawn point
         """
         return EgoVehicle(self.sim_id, self.world, available_car_models[self.model_index], self.get_ego_spawn_point(), self.ego_behavior)

    def restart_with_options(self):
        self.sim_root.ego.model_id = available_car_models[self.model_index]
        self.sim_root.ego.spawn_point = self.map.get_spawn_points()[self.spawn_point_index]
        self.sim_root.restart_requested = True
        self.hud.notification(f"Spawn Point: {self.spawn_point_index}, Model Index: {self.model_index}")

    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):

        # Spawn points of the EGO vehicle can be changed using Left And Right Arrows

        if keyboard_state.was_key_pressed(pygame.K_LEFT):
            self.spawn_point_index -= 1
            if self.spawn_point_index < 0:
                self.spawn_point_index = self.spawn_points_count - 1
            self.restart_with_options()

        if keyboard_state.was_key_pressed(pygame.K_RIGHT):
            self.spawn_point_index += 1
            if self.spawn_point_index >= self.spawn_points_count:
                self.spawn_point_index = 0
            self.restart_with_options()

        if keyboard_state.was_key_pressed(pygame.K_UP):
            self.model_index += 1
            if self.model_index >= len(available_car_models):
                self.model_index = 0
            self.restart_with_options()

        if keyboard_state.was_key_pressed(pygame.K_DOWN):
            self.model_index -= 1
            if self.model_index < 0:
                self.model_index = len(available_car_models) - 1
            self.restart_with_options()

class PersonScenario(SimulationScenario):
    """
    Spawns a single ego vehicle with the given behavior
    """

    def __init__(self, behavior: ActorBehavior, initial_spawn_point: int = 0, initial_model_index = 0):
        self.behavior = behavior
        self.spawn_point_index = initial_spawn_point
        self.model_index = initial_model_index

    def attach(self, sim_root, sim_id: str):
        super().attach(sim_root, sim_id)

        if not self.map.get_spawn_points():
            raise(Exception('There are no spawn points available in your map/town. Please add some Vehicle Spawn Point to your UE4 scene.'))
        self.spawn_points_count = len(self.map.get_spawn_points())

    def get_ego_spawn_point(self):
        spawn_points = self.map.get_spawn_points()
        spawn_point = spawn_points[self.spawn_point_index]
        return spawn_point

    def get_ego_vehicle(self) -> Vehicle:
         """
         Return the ego vehicle at its initial spawn point
         """
         return Person(self.world, "walker.pedestrian.0047", self.get_ego_spawn_point(), self.behavior)

    def restart_with_options(self):
        self.sim_root.ego.model_id = available_car_models[self.model_index]
        self.sim_root.ego.spawn_point = self.map.get_spawn_points()[self.spawn_point_index]
        self.sim_root.restart_requested = True
        self.hud.notification(f"Spawn Point: {self.spawn_point_index}, Model Index: {self.model_index}")

    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):
        pass