from math import pi, sin, cos


# speed, actual_direction, origin_direction, lane, intention, inner_rectangle, pos_x, pos_y, origin_x, origin_y
def next_position(speed, direction, pos_x, pos_y, time_step=0.1, speed_factor=2):
    rad = direction * pi / 180
    pos_x_diff = -sin(rad) * speed * time_step * speed_factor
    pos_y_diff = -cos(rad) * speed * time_step * speed_factor
    return pos_x + pos_x_diff, pos_y + pos_y_diff


# Returns what will be the next speed after accelerating but without making any changes
def next_speed(speed, acc_rate, time_step=0.1, max_speed=20):
    speed_diff = acc_rate * time_step
    new_speed = speed + speed_diff
    if new_speed > max_speed:
        new_speed = max_speed
    elif new_speed < 0:
        new_speed = 0
    return new_speed


def distance_to_inner_intersection(lane, inner_rectangle, pos_x, pos_y):
    top = inner_rectangle.top
    left = inner_rectangle.left
    height = inner_rectangle.h
    width = inner_rectangle.w
    if lane == 0:
        distance = pos_y - (top + height)
    elif lane == 1:
        distance = pos_x - (left + width)
    elif lane == 2:
        distance = top - pos_y
    else:
        distance = left - pos_x
    return distance


def get_virtual_y_position(origin_direction, origin_x, origin_y, pos_x, pos_y):
    """
    Returns the x position of the virtual caravan environment.
    :return: <float> x position at the virtual environment
    """
    rad = origin_direction * pi / 180
    x_real = - 1 * (pos_x - origin_x) * cos(rad)
    y_real = (pos_y - origin_y) * sin(rad)
    return x_real + y_real


def next_direction(speed, actual_direction, origin_direction, lane, intention, inner_rectangle, pos_x, pos_y,
                   origin_x, origin_y):
    from utils.utils import get_right_turn_radio, get_left_turn_radio

    new_direction = actual_direction
    extra_distance = 0
    if intention == "r":
        right_turn_radio = get_right_turn_radio(lane)
        if get_virtual_y_position(origin_direction, origin_x, origin_y, pos_x, pos_y) > -right_turn_radio and \
                distance_to_inner_intersection(lane, inner_rectangle, pos_x, pos_y) <= 0:
            new_direction = turn_direction(speed=speed, radio=right_turn_radio, actual_direction=actual_direction,
                                           intention=intention)
    elif intention == "l":
        left_turn_radio = get_left_turn_radio(lane, extra_distance=extra_distance)
        if get_virtual_y_position(origin_direction, origin_x, origin_y, pos_x, pos_y) < left_turn_radio and \
                distance_to_inner_intersection(lane, inner_rectangle, pos_x, pos_y) + extra_distance <= 0:
            new_direction = turn_direction(speed=speed, radio=left_turn_radio, actual_direction=actual_direction,
                                           intention=intention)
    new_direction = correct_direction(actual_direction=new_direction, intention=intention,
                                      origin_direction=origin_direction)
    return new_direction


# It turns the car to the right or left lane exactly
def turn_direction(speed, radio, actual_direction, intention, turn_degrees=90, time_step=0.1, speed_factor=2):
    direction_change = turn_degrees * speed * time_step * speed_factor / (pi / 2 * radio)
    if intention == 'r':
        new_direction = actual_direction - direction_change
    else:
        new_direction = actual_direction + direction_change
    return new_direction


def correct_direction(actual_direction, intention, origin_direction, turn_degrees=90):
    new_direction = actual_direction
    if intention == 'l':
        target_direction = (origin_direction + turn_degrees) % 360
        cmp = abs(target_direction - abs(actual_direction))
        if cmp != 0.0 and cmp < 2.0:
            new_direction = target_direction
    else:
        target_direction = abs(360 - origin_direction - turn_degrees) % 360
        cmp = abs(target_direction - abs((360 - abs(actual_direction))))
        if cmp != 0.0 and cmp < 2.0:
            new_direction = target_direction
    return new_direction


def total_distance_curve_fix(closest_point, pos_x, pos_y):
    point_x, point_y = closest_point
    x_diff = abs(pos_x - point_x)
    y_diff = abs(pos_y - point_y)
    return x_diff + y_diff


def simulate_next_tick(speed, acc_rate, actual_direction, origin_direction, lane, intention, inner_rectangle,
                       pos_x, pos_y, origin_x, origin_y):
    new_speed = next_speed(speed, acc_rate)
    new_direction = next_direction(new_speed, actual_direction, origin_direction, lane, intention, inner_rectangle,
                                   pos_x, pos_y, origin_x, origin_y)
    new_x, new_y = next_position(speed=new_speed, direction=new_direction, pos_x=pos_x, pos_y=pos_y)
    return new_x, new_y, new_speed, new_direction


def reached_point(point, speed, acc_rate, actual_direction, origin_direction, lane, intention,
                  inner_rectangle, pos_x, pos_y, origin_x, origin_y, extra_distance):
    from utils.utils import get_distance
    point_x, point_y = point
    actual_distance = get_distance(point_x, point_y, pos_x, pos_y)
    new_x, new_y, new_speed, new_direction = simulate_next_tick(speed, acc_rate, actual_direction, origin_direction,
                                                                lane, intention, inner_rectangle, pos_x, pos_y,
                                                                origin_x, origin_y)
    next_tick_distance = get_distance(point_x, point_y, new_x, new_y)
    return next_tick_distance >= actual_distance or actual_distance < extra_distance


"""
def ticks_to_reach_point(point, car_length, speed, acc_rate, actual_direction, origin_direction,
                         lane, intention, inner_rectangle, pos_x, pos_y, origin_x, origin_y):
    ticks = -1
    if not reached_point(point, car_length, speed, acc_rate, actual_direction, origin_direction,
                         lane, intention, inner_rectangle, pos_x, pos_y, origin_x, origin_y) and \
            speed != 0 or acc_rate != 0:
        ticks = 0
        while not reached_point(point, car_length, speed, acc_rate, actual_direction, origin_direction,
                                lane, intention, inner_rectangle, pos_x, pos_y, origin_x, origin_y):
            # Need to check this, may be too random
            if speed < 0.2 and acc_rate <= 0.0:
                ticks = -1
                break
            pos_x, pos_y, speed, actual_direction = simulate_next_tick(speed, acc_rate, actual_direction,
                                                                       origin_direction, lane, intention,
                                                                       inner_rectangle, pos_x, pos_y, origin_x,
                                                                       origin_y)
            ticks += 1
    return ticks



def ticks_to_pass_point(point, car_length, speed, acc_rate, actual_direction, origin_direction,
                        lane, intention, inner_rectangle, pos_x, pos_y, origin_x, origin_y):
    ticks = -1
    if not passed_point(point, car_length, speed, acc_rate, actual_direction, origin_direction,
                        lane, intention, inner_rectangle, pos_x, pos_y, origin_x, origin_y) and \
            speed != 0 or acc_rate != 0:
        ticks = 0
        while not passed_point(point, car_length, speed, acc_rate, actual_direction, origin_direction,
                               lane, intention, inner_rectangle, pos_x, pos_y, origin_x, origin_y):
            # Need to check this, may be too random
            if speed < 0.2 and acc_rate <= 0.0:
                ticks = -1
                break
            pos_x, pos_y, speed, actual_direction = simulate_next_tick(speed, acc_rate, actual_direction,
                                                                       origin_direction, lane, intention,
                                                                       inner_rectangle, pos_x, pos_y, origin_x,
                                                                       origin_y)
            ticks += 1
    return ticks

"""


def passed_point(point, speed, acc_rate, actual_direction, origin_direction, lane, intention,
                 inner_rectangle, pos_x, pos_y, origin_x, origin_y, extra_distance):
    from utils.utils import get_distance
    point_x, point_y = point
    actual_distance = get_distance(point_x, point_y, pos_x, pos_y)
    new_x, new_y, new_speed, new_direction = simulate_next_tick(speed, acc_rate, actual_direction, origin_direction,
                                                                lane, intention, inner_rectangle, pos_x, pos_y,
                                                                origin_x, origin_y)
    next_tick_distance = get_distance(point_x, point_y, new_x, new_y)
    return next_tick_distance >= actual_distance > extra_distance


# Returns the amount of ticks needed to go through the distance to the specified point from the specified position and
# some extra distance if it specified. extra_distance = 0 would mean the ticks to reach the point
def ticks_to_reach_point(pos_x, pos_y, origin_x, origin_y, actual_direction, origin_direction, lane, intention,
                         speed, inner_rectangle, point, acc_rate, extra_distance, time_step=0.1,
                         speed_factor=2):
    from utils.utils import instant_ticks_to_crash
    if reached_point(point, speed, acc_rate, actual_direction, origin_direction, lane, intention,
                     inner_rectangle, pos_x, pos_y, origin_x, origin_y, extra_distance=(1/2) * extra_distance) or \
            speed < 0.2 and acc_rate <= 0.0:
        ticks_to_point = -1
    else:
        aprox_distance = total_distance_curve_fix(point, pos_x, pos_y)
        ticks_to_point = instant_ticks_to_crash(aprox_distance, speed, time_step, speed_factor)
    return ticks_to_point, reached_point(point, speed, acc_rate, actual_direction, origin_direction, lane, intention,
                     inner_rectangle, pos_x, pos_y, origin_x, origin_y, extra_distance=(1/2) * extra_distance)


# Returns the amount of ticks needed to go through the distance to the specified point from the specified position and
# some extra distance if it specified. extra_distance = 0 would mean the ticks to reach the point
def ticks_to_pass_point(pos_x, pos_y, origin_x, origin_y, actual_direction, origin_direction, lane, intention,
                        speed, inner_rectangle, point, acc_rate, extra_distance, time_step=0.1,
                        speed_factor=2):
    from utils.utils import instant_ticks_to_crash
    if passed_point(point, speed, acc_rate, actual_direction, origin_direction, lane, intention,
                    inner_rectangle, pos_x, pos_y, origin_x, origin_y, extra_distance=(3/2) * extra_distance) or \
            speed < 0.2 and acc_rate <= 0.0:
        ticks_to_point = -1
    else:
        aprox_distance = total_distance_curve_fix(point, pos_x, pos_y)
        ticks_to_point = instant_ticks_to_crash(aprox_distance + (3/2) * extra_distance, speed, time_step, speed_factor)
    return ticks_to_point, passed_point(point, speed, acc_rate, actual_direction, origin_direction, lane, intention,
                    inner_rectangle, pos_x, pos_y, origin_x, origin_y, extra_distance=(3/2) * extra_distance)


def collision_free_acceleration(closest_car_ticks_distance, closest_point, speed, pos_x, pos_y):
    distance_to_point = total_distance_curve_fix(closest_point, pos_x, pos_y)
    new_acc = 2 * (distance_to_point - speed * closest_car_ticks_distance) / pow(closest_car_ticks_distance, 2)
    return new_acc


