import pygame
import carla
from carla_kickstart.vehicle import VehicleLight
from carla_kickstart.person import Person
from carla_kickstart.input import KeyboardState
from carla_kickstart.behaviors.base import ActorBehavior

class ManualDrivingBehavior(ActorBehavior):
    """
    Allows driving with W A S D + Space
    """

    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):
       

        if keyboard_state.is_key_down(pygame.K_SPACE):
            self.vehicle.set_light(VehicleLight.Brake, True)
        else:
            self.vehicle.set_light(VehicleLight.Brake, False)

        self.engine.idle()
        self.engine.steer(0)       

class ManualWalkBehavior(ActorBehavior):

    def attach(self, person: Person):
        super().attach(person)
        self.control = person._control
        self.rotation = person.player.get_transform().rotation
        self.player_max_speed = 1.589
        self.player_max_speed_fast = 3.713

    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):
        milliseconds = clock.get_time()

        self.control.jump = keyboard_state.was_key_pressed(pygame.K_SPACE)
        
        self.control.speed = .01
        self.rotation.yaw -= 0.008 * milliseconds
        self.rotation.yaw = round(self.rotation.yaw, 1)
        self.control.direction = self.rotation.get_forward_vector()