import carla
from abc import ABC, abstractmethod
from enum import Enum

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

class VehicleEngine(ABC):

    @abstractmethod
    def accelerate(self, amount: float = 0.01):
        pass

    @abstractmethod
    def brake(self, amount: float = 0.2):
        pass

    @abstractmethod
    def emergency_brake(self):
        pass

    @abstractmethod
    def idle(self):
        pass

    @abstractmethod
    def steerLeft(self):
        pass

    @abstractmethod
    def steerRight(self):
        pass

    @abstractmethod
    def steer(self, amount: float):
        pass

    @abstractmethod
    def is_reverse(self) -> bool:
        pass

    @abstractmethod
    def toggle_reverse(self):
        pass

    @abstractmethod
    def update(self, clock):
        pass

class VehicleBase(ABC):

    @abstractmethod
    def restart(self):
        pass

    @property
    @abstractmethod
    def speed(self) -> float:
        pass

    @property
    @abstractmethod
    def location(self) -> carla.Location:
        pass

    @abstractmethod
    def spawn(self):
        pass

    @abstractmethod
    def attach_sensor(self, name: str, sensor):
        pass

    @abstractmethod
    def setup_default_sensors(self):
        pass

    @abstractmethod
    def has_sensor(self, name):
        pass

    @abstractmethod
    def get_sensor(self, name: str):
        pass

    @abstractmethod
    def set_light(self, which: VehicleLight, on: bool):
        pass

    @abstractmethod
    def update(self, clock, keyboard_state):
        pass

        abstractmethod
    def destroy(self):
        pass