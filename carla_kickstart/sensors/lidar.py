import carla
import weakref
import numpy as np
from carla_kickstart.config import config
import pygame


RENDER_SIZE = (320, 320)

class LidarSensor(object):

    def __init__(self, parent_actor):
        self.sensor = None
        self._parent = parent_actor
        self.world = parent_actor.get_world()

        lidar_bp = self.world.get_blueprint_library().find('sensor.lidar.ray_cast')
        self.range = 15
        lidar_bp.set_attribute('range', str(self.range))
        lidar_bp.set_attribute('dropoff_general_rate', '0')
        lidar_bp.set_attribute('dropoff_intensity_limit', lidar_bp.get_attribute('dropoff_intensity_limit').recommended_values[0])
        lidar_bp.set_attribute('dropoff_zero_intensity', lidar_bp.get_attribute('dropoff_zero_intensity').recommended_values[0])

        lidar_bp.set_attribute('channels', '64')
        lidar_bp.set_attribute('points_per_second', '250000')

        lidar_bp.set_attribute('rotation_frequency', str(config.target_fps))
        lidar_bp.set_attribute("sensor_tick", str(1.0 / 4.0))

        transform = carla.Transform(carla.Location(x=0, z=1.8))

        self.surface = pygame.Surface((0, 0))
        self.frame = 0

        self.sensor = self.world.spawn_actor(lidar_bp, transform, attach_to=parent_actor)

        weak_self = weakref.ref(self)
        self.sensor.listen(lambda point_cloud: LidarSensor._lidar_callback(weak_self, point_cloud))

    @staticmethod
    def _lidar_callback(weak_self, point_cloud):
        """
        Prepares a point cloud with intensity
        colors ready to be consumed by Open3D
        """
        self = weak_self()

        disp_size = RENDER_SIZE
        lidar_range = 2.0*self.range

        # 2D top view
        points = np.frombuffer(point_cloud.raw_data, dtype=np.dtype('f4'))
        points = points.reshape((int(points.shape[0] / 4), 4)) # (x, y, z, intensity)

        # simple ground segmentation
        ground_threshold = -1.5
        ground_indices = np.where(points[:,2] < ground_threshold)[0]
        points = np.delete(points, ground_indices, axis = 0)

        # map point cloud to 2d space (by dropping z)
        lidar_data = np.array(points[:, :2])
        lidar_data *= min(disp_size) / lidar_range
        lidar_data += (0.5 * disp_size[0], 0.5 * disp_size[1])
        lidar_data = np.fabs(lidar_data)  # pylint: disable=E1111
        lidar_data = lidar_data.astype(np.int32)
        #lidar_data = np.reshape(lidar_data, (-1, 2))
        lidar_img_size = (disp_size[0], disp_size[1], 3)

        lidar_img = np.zeros((lidar_img_size), dtype=np.uint8)

        #z = points[:,2]
        #col = (z - np.min(z)) / (np.max(z) - np.min(z)) * 255

        #lidar_img[lidar_data[:,0], lidar_data[:,1], 1] = col

        lidar_img[tuple(lidar_data.T)] = (255, 255, 255)

        self.surface = pygame.surfarray.make_surface(lidar_img)

        self.frame += 1