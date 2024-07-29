from abc import ABC, abstractmethod

class VehicleEngine(ABC):

    @abstractmethod
    def accelerate(self, amount = 0.01):
        pass

    @abstractmethod
    def brake(self, amount = 0.2):
        pass

    @abstractmethod
    def emergency_brake(self):
        pass

    @abstractmethod
    def idle(self):
        pass

    @abstractmethod
    def steerLeft(self, steer_increment):
        pass

    @abstractmethod
    def steerRight(self, steer_increment):
        pass

    @abstractmethod
    def steer(self, amount):
        pass

    @abstractmethod
    def is_reverse(self):
        pass

    @abstractmethod
    def toggle_reverse(self):
        pass

    @abstractmethod
    def update(self, clock):
        pass