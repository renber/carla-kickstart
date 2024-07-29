import carla
import weakref
import numpy as np
from matplotlib import cm
from carla_kickstart.config import RENDER_RESOLUTION
from carla_kickstart.sensors.object_detection import ObjectDetectionSensor
import pygame
from threading import Thread

RENDER_SIZE = (320, 320)

class CameraSensor(object):

    def __init__(self, parent_actor, with_object_detection = False):
        self.sensor = None
        self._parent = parent_actor
        self.world = parent_actor.get_world()

        self.font = pygame.font.Font(pygame.font.get_default_font(), 12)

        camera_bp = self.world.get_blueprint_library().find('sensor.camera.rgb')
        transform = carla.Transform(carla.Location(x=1.6, z=1.7)) # x=1.6, z=1.7

        camera_bp.set_attribute('image_size_x', str(RENDER_SIZE[0]))
        camera_bp.set_attribute('image_size_y', str(RENDER_SIZE[1]))
        #if camera_bp.has_attribute('gamma'):
        #    camera_bp.set_attribute('gamma', str(gamma_correction))

        self.surface = pygame.Surface((0, 0))

        self.sensor = self.world.spawn_actor(camera_bp, transform, attach_to=parent_actor, attachment_type = carla.AttachmentType.Rigid)

        self.detections = []

        weak_self = weakref.ref(self)

        if with_object_detection:
            self.last_frame = None
            self.object_detection = ObjectDetectionSensor()
            thread = Thread(target=run_detection, args=(weak_self,))
            thread.start()
        else:
            self.object_detection = None

        self.sensor.listen(lambda image: CameraSensor._camera_callback(weak_self, image))

    @staticmethod
    def _camera_callback(weak_self, image):
        self = weak_self()

        image.convert(carla.ColorConverter.Raw)
        array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (image.height, image.width, 4))
        array = array[:, :, :3]
        array = array[:, :, ::-1]

        self.last_frame = array
        self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))

        if self.object_detection is not None:
            for d in self.detections:
                pygame.draw.rect(self.surface, (0, 0, 255), d.rect, 1)

                text = self.font.render(d.class_name, True, (0, 0, 255))
                self.surface.blit(text, (d.rect[0], d.rect[1]))

def run_detection(weak_self):
    self = weak_self()

    while True:
        if self.last_frame is not None:
            image = self.last_frame
            detections = self.object_detection.detect(image, RENDER_SIZE)
            self.detections = detections