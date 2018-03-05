
def default_controller(car):
    car.set_acceleration(0)


def accelerating_controller(car):
    car.set_acceleration(2)


def graph_controller(car):
    from models.car import SimulationCar
    from utils.utils import get_collision_point
    self_simulation = SimulationCar(car)
    following_list = car.get_following_cars()
    inner_intersection = None
    full_intersection = None
    collision_y = None
    collision_x = None
    no_speed_zero = True
    max_acceleration = None
    max_distance_in_ticks = -1
    # Checks if list is empty
    if not following_list:
        car.set_controller(accelerating_controller)
        inner_intersection = car.inner_intersection_rectangle
        full_intersection = car.full_intersection_rectangle
    for car_name in following_list:
        details = following_list[car_name]
        pos_x = details['pos_x']
        pos_y = details['pos_y']
        speed = details['speed']
        acceleration = details['acceleration']
        intention = details['intention']
        direction = details['direction']
        lane = details['lane']
        if speed == 0:
            car.set_acceleration(car.minimum_acceleration)
            no_speed_zero = False
            break

        collision_x, collision_y = get_collision_point(lane=car.get_lane(), intention=car.get_intention(),
                                                       other_lane=lane,
                                                       other_intention=intention)
        following_simulation = SimulationCar(name=car_name, pos_x=pos_x, pos_y=pos_y, absolute_speed=speed,
                                             acceleration_rate=acceleration, direction=direction, intention=intention,
                                             lane=lane, inner_intersection=inner_intersection,
                                             full_intersection=full_intersection)
        other_ticks = following_simulation.get_ticks_to_goal(collision_x, collision_y)
        if max_distance_in_ticks < other_ticks:
            max_distance_in_ticks = other_ticks
            max_acceleration = acceleration

    if no_speed_zero:
        # If the car speed is 0 it won't get here, if other_ticks is -1 it means that that car already passed the point
        # The car may have passed the point but still be inside the inner intersection so it is still in the list
        if max_distance_in_ticks != -1:
            self_ticks = self_simulation.get_ticks_to_goal(collision_x, collision_y)
            if max_distance_in_ticks <= self_ticks:
                self_simulation.reset()
                ticks_to_point = max_distance_in_ticks
                fix_acceleration = self_simulation.calculate_new_acceleration(ticks_to_point + 1,
                                                                              collision_x, collision_y)
                car.set_acceleration(fix_acceleration)
        # If the maximum was -1 it means the last car that it is following passed that point, that means it can
        # use its acceleration and not crash
        else:
            car.set_acceleration(max_acceleration)










