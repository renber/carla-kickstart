import carla
import pygame
from carla_kickstart.behaviors.automatic import FollowPredefinedRouteBehavior, RouteWaypoint
from carla_kickstart.behaviors.routing import RouteRecorderBehavior
from carla_kickstart.scenarios.base import SimulationScenario
from carla_kickstart.behaviors.base import ActorBehavior, CompoundBehavior, NullBehavior
from carla_kickstart.behaviors.manual import ManualDrivingBehavior, ManualWalkBehavior
from carla_kickstart.behaviors.autonomous import AutopilotDrivingBehavior, DrivingSafetyBehavior
from carla_kickstart.entities.base import VehicleLight
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
from enum import Enum

EGO_MODEL = 'vehicle.mercedes.coupe_2020'
EGO_SPAWN_POINT = 101

class Signal():

    is_on = False

    def set(self):
        self.is_on = True
        print("Signal set")

    def reset(self):
        self.is_on = False

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
        self.attach_sensor("collision", CollisionSensor(self.player))
        #self.attach_sensor("lane", LaneInvasionSensor(self.player))
        self.attach_sensor("gnss", GnssSensor(self.player))
        self.attach_sensor("imu", IMUSensor(self.player))
        self.attach_sensor("camera_front", CameraSensor(self.player, with_object_detection=True))
        self.attach_sensor("radar", RadarSensor(self.player, draw_points=True))
        self.attach_sensor("lidar", LidarSensor(self.player))

class DemoScenario(SimulationScenario):
    """
    A scenario where a leading vehicle spawns in front of the ego vehicle
    """

    # the distance at which the leading vehicle should be spawned
    signal = Signal()

    def __init__(self):
        self.actors = []

    def attach(self, sim_root, sim_id: str):
        super().attach(sim_root, sim_id)
        if not self.map.get_spawn_points():
            raise(Exception('There are no spawn points available in your map/town. Please add some Vehicle Spawn Point to your UE4 scene.'))
        self.spawn_points_count = len(self.map.get_spawn_points())

    def get_crossing_person(self) -> Person:
        ego_point = self.get_ego_spawn_point()
        location = carla.Location(56, 35.5, ego_point.location.z)
        rotation = carla.Rotation(ego_point.rotation.pitch, ego_point.rotation.yaw, ego_point.rotation.roll)
        person_spawn_point = carla.Transform(location, rotation)
        return Person(self.sim_root.world, "walker.pedestrian.0047", person_spawn_point, CrossingPersonBehavior())

    def get_passing_car(self) -> Vehicle:
        ego_point = self.get_ego_spawn_point()
        location = carla.Location(74, 66.5, ego_point.location.z)
        rotation = carla.Rotation(ego_point.rotation.pitch, ego_point.rotation.yaw + 180, ego_point.rotation.roll)
        vehicle_spawn_point = carla.Transform(location, rotation)
        return Vehicle(self.sim_root.world, 'vehicle.nissan.patrol_2021', vehicle_spawn_point, PassingCarBehavior(self.signal))

    def restart(self):
        super().restart()

        self.signal.reset()

        if len(self.actors) == 0:
            self.actors.append(self.get_crossing_person())
            self.actors.append(self.get_passing_car())

        for actor in self.actors:
            actor.restart()

    def get_ego_spawn_point(self):
        return self.map.get_spawn_points()[EGO_SPAWN_POINT]

    def on_waypoint_reached(self, wp: RouteWaypoint):
        self.safety_behavior.on_situation_detected(wp.state_name, wp.intent)

        if wp.state_name == "AfterZebra":
            # spawn other cars
            self.signal.set()

    def get_ego_vehicle(self) -> Vehicle:
         """
         Return the ego vehicle at its initial spawn point
         """
         #return self.get_passing_car()
         #return self.get_crossing_person()
         # RouteRecorderBehavior("recorded.csv")
         self.safety_behavior = DrivingSafetyBehavior()
         behavior = CompoundBehavior(FollowPredefinedRouteBehavior(filename="scenario.csv", driver_behavior="cautious", waypoint_reached_callback=self.on_waypoint_reached), self.safety_behavior)
         return EgoVehicle(self.sim_id, self.world, EGO_MODEL, self.get_ego_spawn_point(), behavior)

    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):
        super().update(clock, keyboard_state)

        for actor in self.actors:
            actor.update(clock, keyboard_state)

    def destroy(self):
        for actor in self.actors:
            actor.destroy()

        self.actors = []

class CrossingPersonBehavior(ActorBehavior):

    z_corrected = False

    def attach(self, person):
        super().attach(person)
        self.person = person
        self._control = person._control
        self._rotation = person.player.get_transform().rotation
        self.player_max_speed = 1.589
        self.z_corrected = False

        self._rotation.yaw = 180 # start walking in the other direction
        self._control.direction = self._rotation.get_forward_vector()

    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):

        self._control.speed = self.player_max_speed
        if self.person.travelled_distance > 22:
            if  not self.z_corrected:
                # help the pedestrian onto the sidewalk...
                location = self.person.player.get_transform().location
                location.x -= 0.3
                location.z += 0.5
                self.person.player.set_location(location)
                self.z_corrected = True
            else:
                self._control.jump = False

class PassingCarBehavior(ActorBehavior):

    elapsed = 0

    def __init__(self, signal: Signal, delay_ms: int = 0):
        self.signal = signal
        self.started = False
        self.delay_ms = delay_ms

        dest = carla.Location(-5.83, 66.24, 0.00)
        self.__inner_behavior = FollowPredefinedRouteBehavior(waypoints=[RouteWaypoint(dest, 30)])

    def attach(self, vehicle):
        ActorBehavior.attach(self, vehicle)
        self.__inner_behavior.attach(self.vehicle)

    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):
        if not self.started:
            self.started = self.signal.is_on

        if self.started:

            if self.delay_ms > 0:
                self.delay_ms = max(0, self.delay_ms - clock.get_time())
            else:
                self.__inner_behavior.update(clock, keyboard_state)