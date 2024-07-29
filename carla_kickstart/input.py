import pygame
import carla

class KeyboardState:

    def __init__(self):
        self.pressed_keys = set() # key which has been pressed, will be active for one frame
        self.down_keys = set() # keys which are held down

    def update(self, event):
        if event.type == pygame.KEYDOWN:
            self.down_keys.add(event.key)
        elif event.type == pygame.KEYUP:
            if event.key in self.down_keys:
                self.down_keys.remove(event.key)
            self.pressed_keys.add(event.key)

    def reset_pressed_keys(self):
        self.pressed_keys.clear()

    def is_key_down(self, key):
        return key in self.down_keys

    def was_key_pressed(self, key):
        return key in self.pressed_keys

class SystemInputController(object):

    def __init__(self, sim_root, *subcontrollers):
        self.sim_root = sim_root
        self.keyboard_state = KeyboardState()
        self.subcontrollers = subcontrollers

    def update(self, clock):
        for event in pygame.event.get():
            self.keyboard_state.update(event)

            if event.type == pygame.QUIT:
                self.sim_root.exit_requested = True
                return
            elif self.keyboard_state.was_key_pressed(pygame.K_ESCAPE):
                self.sim_root.exit_requested = True
                return
            elif self.keyboard_state.was_key_pressed(pygame.K_r):
                self.sim_root.restart_requested = True

            if self.keyboard_state.was_key_pressed(pygame.K_c):
                self.sim_root.camera_manager.toggle_camera()

            if self.keyboard_state.was_key_pressed(pygame.K_v):
                self.sim_root.camera_manager.next_sensor()


        for c in self.subcontrollers:
            c.update(clock, self.keyboard_state)

    def reset(self):
        self.keyboard_state.reset_pressed_keys()