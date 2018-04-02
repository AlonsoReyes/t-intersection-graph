
def default_controller(car):
    car.set_acceleration(0)


def accelerating_controller(car):
    car.set_acceleration(car.maximum_acceleration)


# Returns the collision point that is closest to the car that owns the controller,
# the data of the car that is closest to that point and the ticks that car takes to pass that point
def get_closest_car(car):
    from utils.utils import get_distance, collision_points  # car_intention, car_lane, follow_intention, follow_lane
    from functions.car_functions import ticks_to_pass_point
    following_list = car.get_following_cars()
    # get points that are possible collision points
    possible_points = []
    intention = car.get_intention()
    lane = car.get_lane()
    pos_x, pos_y = car.get_position()
    for key in following_list:
        following_car = following_list[key]
        if None in list(following_car.values()):
            continue
        following_intention = following_car['intention']
        following_lane = following_car['lane']
        p_set = set(possible_points)
        f_set = collision_points(car_intention=intention, car_lane=lane, follow_intention=following_intention,
                                 follow_lane=following_lane)
        common_points = set(f_set) - p_set
        possible_points = possible_points + list(common_points)
    possible_points = sorted(possible_points, key=lambda p: get_distance(p[0], p[1], pos_x, pos_y))
    closest_point = None
    if possible_points:
        closest_point = possible_points[0]
    closest_car = {}
    closest_car_distance = None
    inner_rectangle = car.inner_intersection_rectangle
    passed = False
    for key in following_list:
        following_car = following_list[key]
        if None in list(following_car.values()):
            continue
        following_intention = following_car['intention']
        following_lane = following_car['lane']
        collisions = collision_points(car_intention=intention, car_lane=lane,
                                      follow_intention=following_intention, follow_lane=following_lane)
        if closest_point in collisions:
            following_x = following_car['pos_x']
            following_y = following_car['pos_x']
            following_origin_x = following_car['origin_x']
            following_origin_y = following_car['origin_y']
            car_length = following_car['car_length']
            following_speed = following_car['speed']
            following_acc_rate = following_car['acceleration']
            following_actual_direction = following_car['direction']
            following_origin_direction = following_car['origin_direction']
            ticks_distance, passed_temp = ticks_to_pass_point(point=closest_point, speed=following_speed,
                                                              actual_direction=following_actual_direction,
                                                              origin_direction=following_origin_direction,
                                                              origin_x=following_origin_x, origin_y=following_origin_y,
                                                              acc_rate=following_acc_rate, lane=following_lane,
                                                              intention=following_intention,
                                                              inner_rectangle=inner_rectangle,
                                                              pos_x=following_x, pos_y=following_y, extra_distance=car_length)
            if closest_car_distance is None or closest_car_distance > ticks_distance:
                closest_car = following_list[key]
                closest_car_distance = ticks_distance
                passed = passed_temp
    return closest_car, closest_car_distance, closest_point, passed


def algorithm_controller(car):
    from functions.car_functions import ticks_to_reach_point, collision_free_acceleration, passed_point
    following_list = car.get_following_cars()

    if not following_list:
        car.set_controller(accelerating_controller)
        car.get_controller()(car)
    else:
        car_length = car.get_car_length()
        speed = car.get_speed()
        acc_rate = car.get_acceleration()
        actual_direction = car.get_direction()
        origin_direction = car.get_origin_direction()
        lane = car.get_lane()
        intention = car.get_intention()
        inner_rectangle = car.inner_intersection_rectangle
        pos_x, pos_y = car.get_position()
        origin_x = car.get_origin_x_coordinate()
        origin_y = car.get_origin_y_coordinate()
        closest_car, closest_car_ticks_distance, closest_point, passed = get_closest_car(car)
        ticks_in_three_seconds = 3 * (1 / (car.get_time_step() * car.get_speed_factor()))
        if closest_point is None:
            return
        ticks_distance, reached = ticks_to_reach_point(point=closest_point, speed=speed, acc_rate=acc_rate,
                                              actual_direction=actual_direction,
                                              origin_direction=origin_direction, lane=lane, intention=intention,
                                              inner_rectangle=inner_rectangle, pos_x=pos_x, pos_y=pos_y,
                                              origin_x=origin_x, origin_y=origin_y, extra_distance=car_length)
        if closest_car_ticks_distance == -1:
            if passed:
                print(car.get_name(), 'passed some shit')
                car.set_controller(accelerating_controller)
                car.get_controller()(car)
            else:
                car.set_acceleration(car.minimum_acceleration)
            # could make it advance to the edge of the intersection if the car isn't inside it yet
        elif ticks_distance - ticks_in_three_seconds <= closest_car_ticks_distance:

            new_acceleration = collision_free_acceleration(closest_car_ticks_distance, closest_point, speed, pos_x,
                                                           pos_y)
            car.set_acceleration(new_acceleration)
