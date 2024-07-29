import weakref
import carla
import math

class RadarPoint:

    def __init__(self, distance_in_meters, horizontal_angle):
        self.horizontal_angle = horizontal_angle
        self.distance_in_meters = distance_in_meters

GOOD_DISTANCE = 20

class RadarSensor(object):

    def __init__(self, parent_actor, draw_points = False):
        self.sensor = None
        self._parent = parent_actor
        bound_x = 0.5 + self._parent.bounding_box.extent.x
        bound_y = 0.5 + self._parent.bounding_box.extent.y
        bound_z = 0.5 + self._parent.bounding_box.extent.z

        self.draw_points = draw_points

        self.velocity_range = 7.5 # m/s
        world = self._parent.get_world()
        self.debug = world.debug
        bp = world.get_blueprint_library().find('sensor.other.radar')
        bp.set_attribute('horizontal_fov', str(20)) # 35
        bp.set_attribute('vertical_fov', str(0)) # 20
        bp.set_attribute('range', str(100))
        self.sensor = world.spawn_actor(
            bp,
            carla.Transform(
                carla.Location(x=bound_x + 0.05, z=bound_z), # z+0.05
                carla.Rotation(pitch=-2)), # 5
            attach_to=self._parent)
        # We need a weak reference to self to avoid circular reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(
            lambda radar_data: RadarSensor._Radar_callback(weak_self, radar_data))

        self.points = []

    @staticmethod
    def _Radar_callback(weak_self, radar_data):
        self = weak_self()
        if not self:
            return
        # To get a numpy [[vel, altitude, azimuth, depth],...[,,,]]:
        # points = np.frombuffer(radar_data.raw_data, dtype=np.dtype('f4'))
        # points = np.reshape(points, (len(radar_data), 4))

        self.points = list([RadarPoint(x.depth, math.degrees(x.azimuth)) for x in radar_data])

        current_rot = radar_data.transform.rotation
        for detect in radar_data:
            azi = math.degrees(detect.azimuth)
            alt = math.degrees(detect.altitude)
            # The 0.25 adjusts a bit the distance so the dots can
            # be properly seen
            fw_vec = carla.Vector3D(x=detect.depth - 0.25)
            carla.Transform(
                carla.Location(),
                carla.Rotation(
                    pitch=current_rot.pitch + alt,
                    yaw=current_rot.yaw + azi,
                    roll=current_rot.roll)).transform(fw_vec)

            # color radar point based on distance to the vehicle
            #def clamp(min_v, max_v, value):
            #    return max(min_v, min(value, max_v))

            #norm_velocity = detect.velocity / self.velocity_range # range [-1, 1]
            #r = int(clamp(0.0, 1.0, 1.0 - norm_velocity) * 255.0)
            #g = int(clamp(0.0, 1.0, 1.0 - abs(norm_velocity)) * 255.0)
            #b = int(abs(clamp(- 1.0, 0.0, - 1.0 - norm_velocity)) * 255.0)

            if detect.depth > GOOD_DISTANCE: # distance in meters
                r = 255
                g = 255
                b = 255
            else:
                r = 255
                g = 0
                b = 0

            if self.draw_points:
                self.debug.draw_point(
                    radar_data.transform.location + fw_vec,
                    size=0.075,
                    life_time=0.06,
                    persistent_lines=False,
                    color=carla.Color(r, g, b))