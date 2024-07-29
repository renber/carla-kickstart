import sys
import carla
import os
import math
import pygame
from carla_kickstart.hud import HUD
from carla_kickstart.input import SystemInputController
from carla_kickstart.behaviors.manual import ManualDrivingBehavior
from carla_kickstart.carla_utils import find_weather_presets, get_actor_display_name
from carla_kickstart.camera import CameraManager
from carla_kickstart.config import config
from carla_kickstart.scenarios.base import SimulationScenario
from carla_kickstart.scenarios.base import SimulationScenario
from carla_kickstart.config import SIM_ID

class DriveApp(object):

    def connect(self, host, port, synchronous: bool):
        '''
        Connects to running Carla Server and retrieves Carla's world object
        '''
        pygame.init()
        pygame.font.init()

        self.client = carla.Client(host, port)
        self.client.set_timeout(5.0)

        self.sim_world = self.client.get_world()
        self._init(synchronous)

        print(f"Simulation ID: {config.sim_id}")


    def _init(self, synchronous: bool):
        settings = self.sim_world.get_settings()
        settings.no_rendering_mode = True
        self.synchronous = synchronous
        if synchronous:
            settings.synchronous_mode = True
            settings.fixed_delta_seconds = 1.0/config.target_fps
        self.sim_world.apply_settings(settings)

        self.hud = HUD(config.window_size[0], config.window_size[1])

    def run(self, scenario: SimulationScenario):
        self.sim_root = SimulationRoot(self.sim_world, self.hud, self.synchronous, scenario)

        display = pygame.display.set_mode( window_size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        display.fill((0,0,0))
        pygame.display.flip()

        if not self.synchronous:
            self.sim_world.wait_for_tick()

        clock = pygame.time.Clock()
        try:
            while not self.sim_root.exit_requested:
                if self.synchronous:
                    self.sim_world.tick()

                clock.tick_busy_loop(60)
                self.sim_root.update(clock)
                self.sim_root.render(display)
                pygame.display.flip()

                if self.sim_root.restart_requested:
                    self.sim_root.restart()
        finally:
            self.sim_root.destroy()

    def quit(self):
        pygame.quit()

        # force quit to end any dangling threads
        os._exit(0)

class SimulationRoot(object):

    def __init__(self, carla_world, hud, synchronous: bool, scenario: SimulationScenario):
        self.world = carla_world
        self.hud = hud
        self.exit_requested = False
        self.restart_requested = False
        self.synchronous = synchronous
        try:
            self.map = self.world.get_map()
        except RuntimeError as error:
            print('RuntimeError: {}'.format(error))
            print('  The server could not send the OpenDRIVE (.xodr) file:')
            print('  Make sure it exists, has the same name of your town, and is correct.')
            sys.exit(1)

        self.clean_up()

        self.controller = SystemInputController(self)

        self.scenario = scenario
        self.scenario.attach(self, config.sim_id)

        self.ego = scenario.get_ego_vehicle()

        self.camera_manager = None
        self._weather_presets = find_weather_presets()
        self._weather_index = 0
        self._gamma = 2.2
        self.restart()
        self.world.on_tick(hud.on_world_tick)
        self.recording_enabled = False
        self.recording_start = 0
        self.constant_velocity_enabled = False
        self.show_vehicle_telemetry = False
        self.doors_are_open = False
        self.current_map_layer = 0
        self.map_layer_names = [
            carla.MapLayer.NONE,
            carla.MapLayer.Buildings,
            carla.MapLayer.Decals,
            carla.MapLayer.Foliage,
            carla.MapLayer.Ground,
            carla.MapLayer.ParkedVehicles,
            carla.MapLayer.Particles,
            carla.MapLayer.Props,
            carla.MapLayer.StreetLights,
            carla.MapLayer.Walls,
            carla.MapLayer.All
        ]

    def clean_up(self):
        """
        Remove actors from previous, crahes simulation runs
        """
        to_del = []
        for actor in self.world.get_actors():
            if 'role_name' in actor.attributes and actor.attributes['role_name'].endswith(config.sim_id):
                to_del.append(actor)

        print("Found %d orphaned actors" % len(to_del))
        for d in to_del:
            d.destroy()

    def restart(self):
        self.restart_requested = False

        # Keep same camera config if the camera manager exists.
        cam_index = self.camera_manager.index if self.camera_manager is not None else 0
        cam_pos_index = self.camera_manager.transform_index if self.camera_manager is not None else 0

        if self.camera_manager is not None:
            self.camera_manager.destroy()
        self.ego.restart()
        self.scenario.restart()
        self.camera_manager = CameraManager(self.ego.player, self.hud, self._gamma)
        self.camera_manager.transform_index = cam_pos_index
        self.camera_manager.set_sensor(cam_index, notify=False, force_respawn=True)
        #actor_type = get_actor_display_name(self.ego.player)

        if self.synchronous:
            self.world.tick()
        else:
            self.world.wait_for_tick()

    def next_weather(self, reverse=False):
        self._weather_index += -1 if reverse else 1
        self._weather_index %= len(self._weather_presets)
        preset = self._weather_presets[self._weather_index]
        self.hud.notification('Weather: %s' % preset[1])
        self.ego.player.get_world().set_weather(preset[0])

    def next_map_layer(self, reverse=False):
        self.current_map_layer += -1 if reverse else 1
        self.current_map_layer %= len(self.map_layer_names)
        selected = self.map_layer_names[self.current_map_layer]
        self.hud.notification('LayerMap selected: %s' % selected)

    def load_map_layer(self, unload=False):
        selected = self.map_layer_names[self.current_map_layer]
        if unload:
            self.hud.notification('Unloading map layer: %s' % selected)
            self.world.unload_map_layer(selected)
        else:
            self.hud.notification('Loading map layer: %s' % selected)
            self.world.load_map_layer(selected)

    def update(self, clock):

        self.controller.update(clock)
        self.scenario.update(clock, self.controller.keyboard_state)
        self.ego.update(clock, self.controller.keyboard_state)

        self.hud.tick(self, clock)

        self.controller.reset()

    def render(self, display):
        self.camera_manager.render(display)
        self.hud.render(self, display)

    def destroy(self):
        self.camera_manager.destroy()

        print ("Destroying world")
        self.scenario.destroy()
        self.ego.destroy()