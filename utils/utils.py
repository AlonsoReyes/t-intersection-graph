from random import randint, uniform
from models.car import Car
from models.sensor import ProximitySensor, DistanceSensor
import pygame
import os
from models.controller import default_controller


white = (255, 255, 255)  # RGB white color representation
black = (0, 0, 0)  # RGB black color representation

os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0, 0)
images_directory = os.path.dirname(os.path.abspath(__file__)) + "/../images/"
intersection_background = pygame.image.load(images_directory + "background.jpg")

# Full intersection positions
background_width = intersection_background.get_width()
background_height = intersection_background.get_height()
background_left_coordinate = 0
background_top_coordinate = 0

# Inner intersection positions
inner_intersection_width = 210
inner_intersection_height = 210
inner_left_coordinate = 280
inner_top_coordinate = 280

# 768 is the width and height, 0 0 is from that point
full_intersection_rect = pygame.Rect(background_left_coordinate, background_top_coordinate,
                                     background_width, background_height)
inner_intersection_rect = pygame.Rect(inner_left_coordinate, inner_top_coordinate,
                                      inner_intersection_width, inner_intersection_height)


# initial positions outside the intersection
# (pos_x, pos_y, direction, lane)
total_of_background_x = background_left_coordinate + background_width
total_of_background_y = background_top_coordinate + background_height
quarter_inner_width = inner_intersection_width / 4
quarter_inner_height = inner_intersection_height / 4

# pos_x, pos_y of spawn point of that lane
lane_0_spawn = [inner_left_coordinate + inner_intersection_width / 2 + inner_intersection_width / 4,
                total_of_background_y + 100]
lane_1_spawn = [total_of_background_x + 100,
                inner_top_coordinate + inner_intersection_height / 2 - inner_intersection_height / 4]
lane_2_spawn = [inner_left_coordinate + inner_intersection_width / 2 - inner_intersection_width / 4,
                background_top_coordinate - 100]
lane_3_spawn = [background_left_coordinate - 100,
                inner_top_coordinate + inner_intersection_height / 2 + inner_intersection_height / 4]

outside_initial_positions = [(lane_0_spawn[0], lane_0_spawn[1], 0, 0),
                             (lane_1_spawn[0], lane_1_spawn[1], 90, 1),
                             (lane_2_spawn[0], lane_2_spawn[1], 180, 2),
                             (lane_3_spawn[0], lane_3_spawn[1], 270, 3)]


# exact points that the cars collision in the entrance/exit of the inner intersection, starting from the bottom
# going counter clockwise, index = lane
entry_collision_points = [(inner_left_coordinate + inner_intersection_width / 2 + inner_intersection_width / 4
                           , inner_top_coordinate + inner_intersection_height),
                          (inner_left_coordinate + inner_intersection_width,
                           inner_top_coordinate + inner_intersection_height / 2 - inner_intersection_height / 4),
                          (inner_left_coordinate + inner_intersection_width / 2 - inner_intersection_width / 4
                           , inner_top_coordinate),
                          (inner_left_coordinate,
                           inner_top_coordinate + inner_intersection_height / 2 + inner_intersection_height / 4)]

exit_collision_points = [(inner_left_coordinate + inner_intersection_width / 2 - inner_intersection_width / 4,
                          inner_top_coordinate + inner_intersection_height),
                         (inner_left_coordinate + inner_intersection_width,
                          inner_top_coordinate + inner_intersection_height / 2 + inner_intersection_height / 4),
                         (inner_left_coordinate + inner_intersection_width / 2 + inner_intersection_width / 4,
                          inner_top_coordinate),
                         (inner_left_coordinate,
                          inner_top_coordinate + inner_intersection_height / 2 - inner_intersection_height / 4)]
# starts from bottom right and goes counter clockwise
inner_square_collision_points = [(outside_initial_positions[i % 4][i % 2],
                                  outside_initial_positions[(i + 1) % 4][(i + 1) % 2])
                                 for i in [3, 0, 1, 2]]

# Circumference collision points starting from the bottom one, then right, top and last the left one
left_turn_collision_points = [(385, 394), (394, 385), (385, 376), (376, 385)]
intersection_points = entry_collision_points + exit_collision_points + inner_square_collision_points + \
                     left_turn_collision_points
intersection_matrix = [{'s': [entry_collision_points[0], exit_collision_points[2],
                              inner_square_collision_points[0], inner_square_collision_points[1]],  # Lane 0
                        'l': [entry_collision_points[0], exit_collision_points[3],
                              inner_square_collision_points[0], inner_square_collision_points[2],
                              left_turn_collision_points[0], left_turn_collision_points[1],
                              left_turn_collision_points[2], left_turn_collision_points[3]],
                        'r': [entry_collision_points[0], exit_collision_points[1],
                              inner_square_collision_points[0]]},
                       {'s': [entry_collision_points[1], exit_collision_points[3],
                              inner_square_collision_points[1], inner_square_collision_points[2]],  # Lane 1
                        'l': [entry_collision_points[1], exit_collision_points[0],
                              inner_square_collision_points[1], inner_square_collision_points[3],
                              left_turn_collision_points[0], left_turn_collision_points[1],
                              left_turn_collision_points[2], left_turn_collision_points[3]],
                        'r': [entry_collision_points[1], exit_collision_points[2],
                              inner_square_collision_points[1]]},
                       {'s': [entry_collision_points[2], exit_collision_points[0],
                              inner_square_collision_points[2], inner_square_collision_points[3]],  # Lane 2
                        'l': [entry_collision_points[2], exit_collision_points[1],
                              inner_square_collision_points[0], inner_square_collision_points[2],
                              left_turn_collision_points[0], left_turn_collision_points[1],
                              left_turn_collision_points[2], left_turn_collision_points[3]],
                        'r': [entry_collision_points[2], exit_collision_points[3],
                              inner_square_collision_points[2]]},
                       {'s': [entry_collision_points[3], exit_collision_points[1],
                              inner_square_collision_points[3], inner_square_collision_points[0]],  # Lane 3
                        'l': [entry_collision_points[3], exit_collision_points[2],
                              inner_square_collision_points[3], inner_square_collision_points[1],
                              left_turn_collision_points[0], left_turn_collision_points[1],
                              left_turn_collision_points[2], left_turn_collision_points[3]],
                        'r': [entry_collision_points[3], exit_collision_points[0],
                              inner_square_collision_points[3]]}]


# returns the points that both cars have to go through
def collision_points(car_intention, car_lane, follow_intention, follow_lane):
    first_points = intersection_matrix[car_lane][car_intention]
    follower_points = intersection_matrix[follow_lane][follow_intention]
    mutual_points = [p for p in first_points if p in follower_points]
    return mutual_points


# gets the radio of the circumference that the car has to follow to turn to the right. Entry point represents
# the X coordinate of where it enters the intersection and exit point the Y coordinate of the side it leaves
def get_right_turn_radio(entry_lane):
    if entry_lane == 0:
        entry_pos = inner_intersection_rect.top + inner_intersection_rect.h
        _, exit_pos, _, _ = outside_initial_positions[(entry_lane + 3) % 4]
    elif entry_lane == 2:
        entry_pos = inner_intersection_rect.top
        _, exit_pos, _, _ = outside_initial_positions[(entry_lane + 3) % 4]
    elif entry_lane == 1:
        entry_pos = inner_intersection_rect.left + inner_intersection_rect.w
        exit_pos, _, _, _ = outside_initial_positions[(entry_lane + 3) % 4]
    else:
        entry_pos = inner_intersection_rect.left
        exit_pos, _, _, _ = outside_initial_positions[(entry_lane + 3) % 4]
    return abs(entry_pos - exit_pos)


def get_left_turn_radio(entry_lane, extra_distance=0):
    if entry_lane == 0:
        entry_pos = abs(inner_intersection_rect.top + inner_intersection_rect.h - extra_distance)
        _, exit_pos, _, _ = outside_initial_positions[(entry_lane + 1) % 4]
    elif entry_lane == 2:
        entry_pos = inner_intersection_rect.top + extra_distance
        _, exit_pos, _, _ = outside_initial_positions[(entry_lane + 1) % 4]
    elif entry_lane == 1:
        entry_pos = abs(inner_intersection_rect.left + inner_intersection_rect.w - extra_distance)
        exit_pos, _, _, _ = outside_initial_positions[(entry_lane + 1) % 4]
    else:
        entry_pos = inner_intersection_rect.left + extra_distance
        exit_pos, _, _, _ = outside_initial_positions[(entry_lane + 1) % 4]
    return abs(entry_pos - exit_pos)


def graph_to_string(car):
    print('Car: ' + str(car.get_name()) + ' Leaf Cars: [' + ' '.join([str(car) for car in car.get_leaf_cars()]) + ']')
    graph = car.get_graph()
    for key in car.get_graph().keys():
        gr = graph[key]
        print(str(gr.get_name()) + ' ' + str(gr.get_lane()) + ' ' + str(gr.get_intention())
              + ' [' + ' '.join([str(car) for car in gr.get_follow_list()]) + ']')


# The list of cars that a car follows is a dictionary where the keys are the names
# and the value is another dictionary with the information of the car that I need to know
def prepare_follow_list(car_list):
    car_dict = {}
    default_dictionary = {'pos_x': None, 'pos_y': None, 'speed': None, 'acceleration': None,
                          'direction': None, 'lane': None, 'intention': None}
    for name in car_list:
        car_dict[name] = dict(default_dictionary)
    return car_dict


# Used in add_new_car method
def delete_from_list(node, node_list):
    for i in range(len(node_list)):
        if node_list[i].get_name() == node.get_name():
            del node_list[i]
            break


# Checks if two cars collide in their trajectory. It is used in Car.add_new_car method
def cars_cross_path(car_lane, car_intention, other_car_lane, other_car_intention):
    """
    Check if the path of one car crosses tih the path o f another. It is true if the other car is the same lane
    or if the other car is in one of the perpendicular lanes.
    :param car_lane: lane of the car
    :param car_intention: intention of a car
    :param other_car_intention: the intention of way of the other car
    :param other_car_lane: the lane at which the other car star its way.
    :return: True if the paths does not crosses, False otherwise.
    """
    lane_to_int_dict = {"l": 0, "s": 1, "r": 2}
    table0 = [[True, True, True], [True, True, True], [True, True, True]]
    table1 = [[True, True, False], [True, True, False], [False, True, False]]
    table2 = [[True, True, True], [True, False, False], [True, False, False]]
    table3 = [[True, True, False], [True, True, True], [False, False, False]]
    all_tables = [table0, table1, table2, table3]
    return all_tables[(car_lane - other_car_lane) % 4][lane_to_int_dict[car_intention]][
        lane_to_int_dict[other_car_intention]]


def do_round(cars, channel):
    channel.do_round()
    for car in cars:
        car.update()


def random_car(name, channel, pos_x=None, pos_y=None, initial_acceleration_rate=None, min_acceleration = 0.0,
               max_acceleration = 5.0, initial_speed=None,
               min_speed=0, max_speed=20, creation_time=0, number_of_lanes=4,
               full_intersection=full_intersection_rect,
               inner_intersection=inner_intersection_rect, create_sensor_flag=False,
               controller=default_controller, **kwargs):
    """
    Generates a random car with the given name. The max speed is used to give an speed not giver than the maximum a the
    car. the lane can be passed in kwargs value if the lane wants to be specified.
    Example: "random_car(4,20,lane=3)"
    :param controller: function which controls if the car needs to speed up or slow down depending of what is
    defined in the function
    :param create_sensor_flag: specifies if the car needs to be created with a sensor, False is used for some tests
    :param number_of_lanes: number of lanes at the simulation
    :param pos_x: x coordinate of spawn
    :param pos_y: y coordinate of spawn
    :param acceleration_rate: initial acceleration
    :param initial_speed: initial speed of the car when it spawns
    :param creation_time: creation car of the car
    :param name: name of the car.
    :param channel: channel which the car sends its messages through
    :param min_speed: minimum speed of a car.
    :param max_speed: maximum speed of the car.
    :param full_intersection: rectangle that represents the full screen of the display
    :param inner_intersection: rectangle that represents the area where collisions can happen when cars turn
    :param kwargs: the lane can be passed in this argument in the "lane" argument.
    :return: a Car object.
    """
    if "lane" in kwargs:
        tmp_x, tmp_y, direction, lane = outside_initial_positions[kwargs["lane"]]

    else:
        new_lane = randint(0, number_of_lanes - 1)
        tmp_x, tmp_y, direction, lane = outside_initial_positions[new_lane]
    if initial_speed is None:
        initial_speed = randint(min_speed, max_speed)
    if initial_acceleration_rate is None:
        initial_acceleration_rate = uniform(min_acceleration, max_acceleration)
    if "initial_speed" in kwargs:
        initial_speed = kwargs["initial_speed"]
    if "intention" in kwargs:
        intention = kwargs["intention"]
    else:
        intention = "s"
        if number_of_lanes == 4:
            random_intention = randint(0, 2)
            if random_intention == 0:
                intention = "l"
            elif random_intention == 1:
                intention = "r"
    if pos_x is None:
        pos_x = tmp_x
    if pos_y is None:
        pos_y = tmp_y
    return Car(name, pos_x, pos_y, acceleration_rate=initial_acceleration_rate,
               channel=channel, direction=direction, lane=lane, absolute_speed=initial_speed,
               intention=intention, creation_time=creation_time, full_intersection=full_intersection,
               inner_intersection=inner_intersection, sensor_flag=create_sensor_flag, controller=controller)


def fix_acceleration(ticks_to_crash, actual_speed, time_step=0.1, other_speed=0, speed_factor=2):
    # solve for acceleration: actual_speed + acceleration * time_step * ticks_to_crash * speed_factor = other_speed
    new_acceleration = (other_speed - actual_speed) / float(ticks_to_crash*time_step*speed_factor)
    return new_acceleration


# Returns how many ticks it would take to go through that distance with that speed in a straight line
def instant_ticks_to_crash(distance, speed, time_step, speed_factor):
    return distance / float(time_step * speed_factor * speed)


def create_sensor(owner_car):
    return DistanceSensor(owner_car=owner_car)


def get_distance(x, y, x_2, y_2):
    from math import sqrt
    return sqrt(pow(x - x_2, 2) + pow(y - y_2, 2))


def draw_collision_points(screen):
    green_dot = pygame.image.load(images_directory + "green_light.jpg")
    green_dot = pygame.transform.scale(green_dot, (5, 5))
    for p in intersection_points:
        g = green_dot.copy()
        g_rect = g.get_rect()
        g_rect.center = p
        screen.blit(g, g_rect)


# Returns the acceleration the car needs to get to the other car's position with 0 speed in what should be N seconds
def n_seconds_fix(distance, ticks_in_one_second, speed, n=3, time_step=0.1, speed_factor=2):
    ticks_left_to_crash = instant_ticks_to_crash(distance, speed, time_step, speed_factor)
    minimum_distance_in_ticks = ticks_in_one_second * n
    ticks_distance = ticks_left_to_crash - minimum_distance_in_ticks
    new_acc = fix_acceleration(ticks_to_crash=ticks_distance, actual_speed=speed)
    return new_acc


def init_graphic_environment(screen_width=background_width, screen_height=background_height):
    """
    Initialize the graphic environment.
    :param screen_width: width of the screen.
    :param screen_height: height of the screen.
    :return: the screen, the backgrounds and the font.
    """
    pygame.init()
    pygame.display.set_icon(intersection_background)
    screen = pygame.display.set_mode((screen_width, screen_height))
    background = pygame.Surface(screen.get_size())
    background = background.convert(background)
    background.fill(white)
    font = pygame.font.SysFont('Arial', 20)
    pygame.display.set_caption('Car simulation')

    return screen, background, intersection_background, font
