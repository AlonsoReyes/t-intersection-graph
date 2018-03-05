from math import pi, cos, sin


# Simulates having a sensor which tells you to stop close to the cars in the same lane
# Used when the cars spawn and when they exit, the closest car is set in those two moments.
# The way it's going to be used is only on the lanes. When a car spawns the sensor will be assigned
# the last car to have spawned in that lane and it watches that car until it enters the inner intersection.
# Then when the owner car leaves the intersection the sensor is assigned another car to be aware of which
# will be the last car to leave the intersection through that lane.
class ProximitySensor(object):

    def __init__(self, owner_car, closest_car=None, limit_distance=30):
        # Car object which represents the car that has the sensor. The sensor gives instructions to this car
        self.owner_car = owner_car
        # Car object which represents the closest car in front/to follow
        self.closest_car = closest_car
        # Minimum distance that cars can have with each other
        self.limit_distance = limit_distance
        if owner_car is not None:
            self.limit_distance = owner_car.get_car_length()

    def get_owner_car(self):
        return self.owner_car

    def set_owner_car(self, car):
        self.owner_car = car

    def get_closest_car(self):
        return self.closest_car

    def set_closest_car(self, car):
        self.closest_car = car

    # Returns the correct value of the position condition depending on the lane
    def sensor_condition(self, pos_x, pos_y, rad, other_x, other_y, other_rad):
        from utils.utils import get_distance
        back_car_length = self.get_owner_car().get_car_length() / 2.0
        front_car_length = self.get_closest_car().get_car_length() / 2.0
        front_car_x = other_x + sin(other_rad) * front_car_length
        front_car_y = other_y + cos(other_rad) * front_car_length
        back_car_x = pos_x - sin(rad) * back_car_length
        back_car_y = pos_y - cos(rad) * back_car_length
        distance = get_distance(front_car_x, front_car_y, back_car_x, back_car_y)
        return distance > self.limit_distance

    def ticks_to_crash(self):
        pos_x, pos_y = self.owner_car.get_position()
        other_x, other_y = self.closest_car.get_position()
        rad = self.owner_car.get_direction() * pi / 180
        other_rad = self.closest_car.get_direction() * pi / 180
        speed_factor = self.owner_car.get_speed_factor()
        time_step = self.owner_car.get_time_step()
        condition = self.sensor_condition(pos_x, pos_y, rad, other_x, other_y, other_rad)
        ticks = 0
        while condition:
            pos_x += -sin(rad) * self.owner_car.get_speed() * time_step * speed_factor
            other_x += -sin(other_rad) * self.closest_car.get_speed() * time_step * speed_factor
            pos_y += -cos(rad) * self.owner_car.get_speed() * time_step * speed_factor
            other_y += -cos(other_rad) * self.closest_car.get_speed() * time_step * speed_factor
            rad = self.owner_car.get_direction() * pi / 180
            other_rad = self.closest_car.get_direction() * pi / 180
            ticks += 1
            condition = self.sensor_condition(pos_x, pos_y, rad, other_x, other_y, other_rad)
        return ticks

    def limit_min_speed(self):
        limit = 0
        if self.owner_car.get_direction() in [0, 180]:
            limit = abs(self.owner_car.full_intersection_rectangle.top
                        - self.owner_car.full_intersection_rectangle.height)
        elif self.owner_car.get_direction() in [90, 270]:
            limit = abs(self.owner_car.full_intersection_rectangle.left
                        - self.owner_car.full_intersection_rectangle.width)
        return limit * 0.002

    def watch(self):
        from utils.utils import fix_acceleration
        limit_min_speed = self.limit_min_speed()

        if self.closest_car is not None:
            if not self.owner_car.check_left_inner_intersection() and self.closest_car.inside_inner_intersection():
                self.set_closest_car(None)
        if self.closest_car is not None:
            other_speed = self.closest_car.get_speed()
            speed = self.owner_car.get_speed()
            time_step = self.owner_car.get_time_step()
            if abs(speed - other_speed) < limit_min_speed:
                self.owner_car.set_acceleration(0)
                self.owner_car.set_speed(other_speed)
            elif other_speed < speed:
                #print(self.owner_car.get_name())
                tick_left_to_crash = self.ticks_to_crash()  # if ticks left to crash is 0 then it's already doomed
                new_acceleration = fix_acceleration(tick_left_to_crash - 1, speed, time_step, other_speed)
                self.owner_car.set_acceleration(new_acceleration)

