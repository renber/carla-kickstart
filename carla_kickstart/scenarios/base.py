from abc import ABC, abstractmethod
from carla_kickstart.vehicle import Vehicle
import pygame
from carla_kickstart.input import KeyboardState

class SimulationScenario(ABC):

    def attach(self, sim_root, sim_id: str):
        self.sim_root = sim_root
        self.world = sim_root.world
        self.map = sim_root.map
        self.hud = sim_root.hud
        self.sim_id = sim_id

    @abstractmethod
    def get_ego_vehicle(self) -> Vehicle:
        pass

    def restart(self):
        pass

    def destroy(self):
        pass

    def update(self, clock: pygame.time.Clock, keyboard_state: KeyboardState):
        # implement in base class if needed
        pass