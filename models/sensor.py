from math import pi, cos, sin


# Simulates having a sensor which tells you to stop close to the cars in the same lane
# Used when the cars spawn and when they exit, the closest car is set in those two moments.
# The way it's going to be used is only on the lanes. When a car spawns the sensor will be assigned
# the last car to have spawned in that lane and it watches that car until it enters the inner intersection.
# Then when the owner car leaves the intersection the sensor is assigned another car to be aware of which
# will be the last car to leave the intersection through that lane.
class ProximitySensor(object):

    def __init__(self, owner_car, closest_car=None, limit_distance=10):
        # Car object which represents the car that has the sensor. The sensor gives instructions to this car
        self.owner_car = owner_car
        # Car object which represents the closest car in front/to follow
        self.closest_car = closest_car
        # Minimum distance that cars can have with each other
        self.limit_distance = limit_distance
        if owner_car is not None:
            self.limit_distance = owner_car.get_car_length() / 4

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

    # When the speed of a car reaches this limit it instantly becomes 0, otherwise the car never stops moving
    def limit_min_speed(self, epsilon=0.002):
        limit = abs(self.owner_car.full_intersection_rectangle.top - self.owner_car.full_intersection_rectangle.height)
        return limit * epsilon

    # It controls the car. Works like the controller, but just in the lanes
    def watch(self):
        from utils.utils import fix_acceleration
        limit_min_speed = self.limit_min_speed()

        if self.closest_car is not None:
            if not self.owner_car.check_left_inner_intersection() and self.closest_car.full_inside_inner_intersection():
                self.set_closest_car(None)
        if self.closest_car is not None:
            other_speed = self.closest_car.get_speed()
            speed = self.owner_car.get_speed()
            time_step = self.owner_car.get_time_step()
            if speed < limit_min_speed:
                self.owner_car.set_acceleration(0)
                self.owner_car.set_speed(other_speed)
            elif other_speed < speed:
                tick_left_to_crash = self.ticks_to_crash()  # if ticks left to crash is 0 then it's already doomed
                if tick_left_to_crash == 0.0:
                    # print([self.closest_car.get_position(), self.closest_car.get_speed(),
                    #       self.closest_car.get_acceleration()])
                    # print([self.owner_car.get_position(), self.owner_car.get_speed(), self.owner_car.get_acceleration()])
                    self.owner_car.set_acceleration(0)
                    self.owner_car.set_speed(other_speed)
                else:
                    new_acceleration = fix_acceleration(tick_left_to_crash, speed, time_step, other_speed,
                                                        self.owner_car.get_speed_factor())
                    self.owner_car.set_acceleration(new_acceleration)


class DistanceSensor(object):

    def __init__(self, owner_car, closest_car=None):
        # Car object which represents the car that has the sensor. The sensor gives instructions to this car
        self.owner_car = owner_car
        # Car object which represents the closest car in front/to follow
        self.closest_car = closest_car
        # Minimum distance that cars can have with each other
        self.limit_distance = owner_car.get_car_length() / 2
        # Last distance measured between cars
        self.last_distance = None
        # Rate in which the acceleration will change
        self.acceleration_change_rate = 0.3

        # How many ticks there are in a second
        self.one_second_ticks = 1 / (owner_car.TIME_STEP * owner_car.SPEED_FACTOR)

    def get_owner_car(self):
        return self.owner_car

    def set_owner_car(self, car):
        self.owner_car = car

    def get_closest_car(self):
        return self.closest_car

    def set_closest_car(self, car):
        self.closest_car = car

    def get_last_distance(self):
        return self.last_distance

    def set_last_distance(self, distance):
        self.last_distance = distance

    def get_acceleration_change_rate(self):
        return self.acceleration_change_rate

    def set_acceleration_change_rate(self, acc):
        self.acceleration_change_rate = acc

    def get_limit_distance(self):
        return self.limit_distance

    def set_limit_distance(self, distance):
        self.limit_distance = distance

    def limit_min_speed(self, epsilon=0.002):
        limit = abs(self.owner_car.full_intersection_rectangle.top - self.owner_car.full_intersection_rectangle.height)
        return limit * epsilon

    def get_back_front_distance(self):
        from utils.utils import get_distance
        pos_x, pos_y = self.owner_car.get_position()
        other_x, other_y = self.closest_car.get_position()
        rad = self.owner_car.get_direction() * pi / 180
        other_rad = self.closest_car.get_direction() * pi / 180
        back_car_length = self.get_owner_car().get_car_length() / 2.0
        front_car_length = self.get_closest_car().get_car_length() / 2.0
        front_car_x = other_x + sin(other_rad) * front_car_length
        front_car_y = other_y + cos(other_rad) * front_car_length
        back_car_x = pos_x - sin(rad) * back_car_length
        back_car_y = pos_y - cos(rad) * back_car_length
        distance = get_distance(front_car_x, front_car_y, back_car_x, back_car_y)
        return distance

    def speed_down_car(self, default_speed_down=-2):
        old_acc = self.get_owner_car().get_acceleration()
        if old_acc <= 0.1:
            new_acc = default_speed_down
        else:
            new_acc = old_acc - abs(old_acc * self.acceleration_change_rate)
        return new_acc

    def speed_up_car(self, default_speed_up=2):
        old_acc = self.get_owner_car().get_acceleration()
        if old_acc <= 0.1:
            new_acc = default_speed_up
        else:
            new_acc = old_acc + abs(old_acc * self.acceleration_change_rate)
        return new_acc

    def use_breaks(self):
        return self.get_owner_car().minimum_acceleration

    def start_up(self, start_acc=2):
        self.get_owner_car().set_acceleration(start_acc)

    def slow_down_condition(self, distance):
        condition = False
        if distance <= self.get_limit_distance():
            condition = True
        return condition

    def speed_up_condition(self, distance):
        condition = False
        if distance > self.get_limit_distance():
            condition = True
        return condition

    def watch(self):
        from utils.utils import n_seconds_fix
        if self.closest_car is not None:
            if self.closest_car.crossed_entrance():
                self.set_closest_car(None)
            elif not self.closest_car.inside_full_rectangle and self.closest_car.left_inner_rectangle and not \
                    self.closest_car.inside_full_intersection():
                self.set_closest_car(None)
        if self.closest_car is not None:
            current_distance = self.get_back_front_distance()
            safe_distance = current_distance + self.limit_distance
            emergency_slow_down = self.slow_down_condition(current_distance)
            speed = self.get_owner_car().get_speed()
            limit_min_speed = self.limit_min_speed()
            other_speed = self.closest_car.get_speed()
            # It's getting closer
            if emergency_slow_down:
                new_acc = self.use_breaks()
            elif speed < limit_min_speed:
                new_acc = 0
                self.owner_car.set_speed(other_speed)
            else:
                new_acc = n_seconds_fix(distance=safe_distance, speed=speed, ticks_in_one_second=self.one_second_ticks,
                                        n=3)
            self.get_owner_car().set_acceleration(new_acc)
            self.set_last_distance(current_distance)
        #if self.get_owner_car().get_name() == 25:
         #   print(self.get_closest_car().get_position(), self.get_closest_car().get_name(), self.get_owner_car().get_position())

