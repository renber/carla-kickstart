from carla_kickstart.simulation import DriveApp
from carla_kickstart.behaviors.base import CompoundBehavior
from carla_kickstart.scenarios.single import SingleEgoVehicleScenario
from carla_kickstart.behaviors.manual import ManualDrivingBehavior
import traceback

HOST = '127.0.0.1'
PORT = 2000

if __name__ == "__main__":
    try:
        app = DriveApp()
        app.connect(HOST, PORT, synchronous=True)

        scenario = SingleEgoVehicleScenario(ManualDrivingBehavior(), initial_spawn_point=30)

        app.run(scenario)
    except Exception:
        traceback.print_exc()
    finally:
        app.quit()