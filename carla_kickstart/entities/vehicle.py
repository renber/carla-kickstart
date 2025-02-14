import math
import random
import carla
from carla_kickstart.basetypes import VehicleEngine
from carla_kickstart.carla_utils import get_actor_blueprints, get_actor_display_name
from carla_kickstart.config import config
from carla_kickstart.behaviors.base import ActorBehavior
from enum import Enum

ACTOR_FILTER = 'vehicle.*'

class VehicleLight(Enum):
    Position = carla.VehicleLightState.Position
    LowBeam = carla.VehicleLightState.LowBeam
    HighBeam = carla.VehicleLightState.HighBeam
    Brake = carla.VehicleLightState.Brake
    RightBlinker = carla.VehicleLightState.RightBlinker
    LeftBlinker = carla.VehicleLightState.LeftBlinker
    Reverse = carla.VehicleLightState.Reverse
    Fog = carla.VehicleLightState.Fog
    Interior = carla.VehicleLightState.Interior
    Special1 = carla.VehicleLightState.Special1
    Special2 = carla.VehicleLightState.Special2

class DefaultEngineModel(VehicleEngine):

    def __init__(self, ego):
        self.ego = ego

        if isinstance(ego.player, carla.Vehicle):
            self._control = carla.VehicleControl()
            self._control.reverse = False
            self._control.gear = 1
            self._steer_cache = 0
            self._steer_change = 0
            self._throttle_change = 0
            self._brake_change = 0

            self.update(None)
        else:
            raise NotImplementedError("Actor type not supported")

    def accelerate(self, amount = 0.001):
        self._control.brake_change = 0
        self._throttle_change = amount

    def brake(self, amount = 0.002):
        self._control.throttle = 0
        self._brake_change = amount

    def emergency_brake(self):
        self._control.throttle = 0
        self._control.brake = 30
        self._control.steer = 0
        self._control.hand_brake = True

    def idle(self):
        '''
        Neither accelerate nor brake
        '''
        self._control.brake = 0
        self._control.throttle = 0

    def steerLeft(self):
        self._steer_change = - 5e-4

    def steerRight(self):
        self._steer_change =  5e-4

    def steer(self, amount):
        self._steer_change = 0
        self._steer_cache = amount

        amount = min(0.7, max(-0.7, amount))
        amount = round(amount, 1)
        self._control.steer = amount
        return amount

    def is_reverse(self):
        return self._control.reverse

    def toggle_reverse(self):
        self._control.reverse = self._control.gear < 0
        self._control.gear = 1 if self._control.reverse else -1

    def update(self, clock):
        '''
        Apply the issued commands
        '''
        if clock is None:
            milliseconds = 0
        else:
            milliseconds = clock.get_time()

        if self._throttle_change > 0:
             amount = self._throttle_change * milliseconds
             self._control.throttle = max(0.7, min(self._control.throttle + amount, 1.00)) # skip deadpoint
             self._throttle_change = 0
             self._control.brake = 0

        if self._brake_change > 0:
            amount = self._brake_change * milliseconds
            self._control.brake = min(self._control.brake + amount, 5)
            self._brake_change = 0
            self._control.throttle = 0

        if self._steer_change != 0:
            amount = self._steer_cache + (self._steer_change * milliseconds)
            self.steer(amount)
            self._steer_change = 0

        self.ego.player.apply_control(self._control)

class Vehicle:

    def __init__(self, world, model_id: str, spawn_point, behavior: ActorBehavior):
        self.world = world
        self.spawn_point = spawn_point
        self.model_id = model_id
        self.model_color_index = 1
        self.actor_role_name = "VEHICLE_" + config.sim_id
        self.player = None
        self.sensors = {}
        self.behavior = behavior
        self.lights = carla.VehicleLightState.NONE
        self._model_lights = None
        self.travelled_distance = 0
        self.last_location = None

    def restart(self):
        self.max_speed = 1.589
        self.max_speed_fast = 3.713
        self.travelled_distance = 0
        self.last_location = None

        self.spawn()

    def _prepare_blueprint(self):
        available_actors = get_actor_blueprints(self.world, ACTOR_FILTER)
        blueprint = next(filter(lambda x: x.id == self.model_id, available_actors))
        blueprint.set_attribute('role_name', self.actor_role_name)
        if blueprint.has_attribute('terramechanics'):
            blueprint.set_attribute('terramechanics', 'true')
        if blueprint.has_attribute('color'):
            available_colors = blueprint.get_attribute('color').recommended_values
            if len(available_colors) > self.model_color_index:
                blueprint.set_attribute('color', available_colors[self.model_color_index]) # color index 0 is white
        if blueprint.has_attribute('driver_id'):
            driver_id = random.choice(blueprint.get_attribute('driver_id').recommended_values)
            blueprint.set_attribute('driver_id', driver_id)
        if blueprint.has_attribute('is_invincible'):
            blueprint.set_attribute('is_invincible', 'false')
        if blueprint.has_attribute('speed'):
            self.max_speed = float(blueprint.get_attribute('speed').recommended_values[1])
            self.max_speed_fast = float(blueprint.get_attribute('speed').recommended_values[2])

        return blueprint

    @property
    def speed(self):
        v = self.player.get_velocity()
        return 3.6 * math.sqrt(v.x**2 + v.y**2 + v.z**2)

    def spawn(self):
        # Get a random blueprint.
        blueprint = self._prepare_blueprint()

        if self.player is not None:
            self.destroy()

        self.player = self.world.try_spawn_actor(blueprint, self.spawn_point)

        if self.player is None:
            raise(Exception(f"Could not spawn Vehicle {self.actor_role_name} at the given location"))

        self.show_vehicle_telemetry = False
        self.modify_vehicle_physics(self.player)

        self.setup_default_sensors()
        self.engine = DefaultEngineModel(self)
        self.behavior.attach(self)

    def attach_sensor(self, name: str, sensor):
        self.sensors[name.lower()] = sensor

    def setup_default_sensors(self):
        # override in child class
        pass

    def has_sensor(self, name):
        return name in self.sensors

    def get_sensor(self, name: str):
        if name in self.sensors:
            return self.sensors[name.lower()]
        else:
            return None

    def set_light(self, which: VehicleLight, on: bool):
        if on:
            self.lights |= which.value
        else:
            self.lights &= ~which.value

    def modify_vehicle_physics(self, actor):
        #If actor is not a vehicle, we cannot use the physics control
        try:
            physics_control = actor.get_physics_control()
            physics_control.use_sweep_wheel_collision = True
            actor.apply_physics_control(physics_control)
        except Exception:
            pass

    def update(self, clock, keyboard_state):
        self.behavior.update(clock, keyboard_state)
        self.engine.update(clock)

        if self.lights != self._model_lights:
            self.player.set_light_state(carla.VehicleLightState(self.lights))
            self._model_lights = self.lights

        if self.last_location is None:
            self.last_location = self.player.get_transform().location
        else:
           current_location = self.player.get_transform().location
           self.travelled_distance += self.last_location.distance(current_location)
           self.last_location = current_location

    def destroy(self):
        self.behavior.detach()

        for sensor in self.sensors.values():
            if sensor is not None:
                sensor.sensor.stop()
                sensor.sensor.destroy()
        if self.player is not None:
            self.player.destroy()