import math
import random
import carla
from carla_kickstart.basetypes import VehicleEngine
from carla_kickstart.carla_utils import get_actor_blueprints, get_actor_display_name
from carla_kickstart.config import config
from carla_kickstart.behaviors.base import ActorBehavior

ACTOR_FILTER = 'walker.pedestrian.*'
ACTOR_GENERATION = '2'

class Person:
    """
    Represents a person / pedestrian
    """

    def __init__(self, world, model_id: str, spawn_point, behavior: ActorBehavior):
        self.world = world
        self.spawn_point = spawn_point
        self.model_id = model_id
        self.model_color_index = 1
        self.actor_role_name = "PERSON_" + config.sim_id
        self.player = None
        self.behavior = behavior
        self._control = carla.WalkerControl()
        self.travelled_distance = 0
        self.last_location = None

    def restart(self):
        self.spawn()
        self.travelled_distance = 0
        self.last_location = None

    def _prepare_blueprint(self):
        available_actors = get_actor_blueprints(self.world, ACTOR_FILTER, ACTOR_GENERATION)
        blueprint = next(filter(lambda x: x.id == self.model_id, available_actors))
        blueprint.set_attribute('role_name', self.actor_role_name)
        if blueprint.has_attribute('color'):
            available_colors = blueprint.get_attribute('color').recommended_values
            if len(available_colors) > self.model_color_index:
                blueprint.set_attribute('color', available_colors[self.model_color_index]) # color index 0 is white
        if blueprint.has_attribute('is_invincible'):
            blueprint.set_attribute('is_invincible', 'false')

        return blueprint

    def spawn(self):
        # Get a random blueprint.
        blueprint = self._prepare_blueprint()

        if self.player is not None:
            self.destroy()

        self.player = self.world.try_spawn_actor(blueprint, self.spawn_point)

        if self.player is None:
            raise(Exception(f"Could not spawn person {self.actor_role_name} at the given location"))

        self.behavior.attach(self)

    def has_sensor(self, name):
        return False

    def get_sensor(self, name: str):
        return None

    def update(self, clock, keyboard_state):
        self.behavior.update(clock, keyboard_state)
        self.player.apply_control(self._control)

        if self.last_location is None:
            self.last_location = self.player.get_transform().location
        else:
           current_location = self.player.get_transform().location
           self.travelled_distance += self.last_location.distance(current_location)
           self.last_location = current_location

    def destroy(self):
        if self.player is not None:
            self.player.destroy()