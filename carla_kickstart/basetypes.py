from abc import ABC, abstractmethod

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