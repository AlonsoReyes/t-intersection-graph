from random import randint
from models.car import Car
from models.sensor import ProximitySensor
import pygame
import os
from models.controller import default_controller

full_intersection_rect = pygame.Rect(0, 0, 768, 768)  # 768 is the width and height, 0 0 is from that point
inner_intersection_rect = pygame.Rect(280, 280, 210, 210)
white = (255, 255, 255)  # RGB white color representation
black = (0, 0, 0)  # RGB black color representation
# initial positions inside the intersection
inside_initial_positions = [(435, 760, 0, 0), (760, 345, 90, 1), (345, 10, 180, 2), (10, 435, 270, 3)]
# initial positions outside the intersection to simulate that the cars enter it
outside_initial_positions = [(435, 868, 0, 0), (868, 335, 90, 1), (335, -98, 180, 2), (-98, 435, 270, 3)]


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


def random_car(name, channel, pos_x=None, pos_y=None, acceleration_rate=0.0,
               initial_speed=None, min_speed=0, max_speed=20, creation_time=0, number_of_lanes=4,
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
    return Car(name, pos_x, pos_y, acceleration_rate=acceleration_rate,
               channel=channel, direction=direction, lane=lane, absolute_speed=initial_speed,
               intention=intention, creation_time=creation_time, full_intersection=full_intersection,
               inner_intersection=inner_intersection, sensor_flag=create_sensor_flag, controller=controller)


def fix_acceleration(ticks_to_crash, actual_speed, time_step, other_speed=0):
    # solve: actual_speed + acceleration * time_step * ticks_to_crash = 0
    new_acceleration = (other_speed - actual_speed) / float(ticks_to_crash*time_step)
    return new_acceleration


def create_sensor(owner_car):
    return ProximitySensor(owner_car=owner_car)


# Returns the coordinates of the point in the intersection where the cars with that characteristics may collide
def get_collision_point(lane, intention, other_lane, other_intention):
    pass


def get_distance(x, y, x_2, y_2):
    from math import sqrt
    return sqrt(pow(x - x_2, 2) + pow(y - y_2, 2))


def init_graphic_environment(screen_width, screen_height):
    """
    Initialize the graphic environment.
    :param screen_width: width of the screen.
    :param screen_height: height of the screen.
    :return: the screen, the backgrounds and the font.
    """
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0, 0)
    images_directory = os.path.dirname(os.path.abspath(__file__)) + "/../images/"
    intersection_background = pygame.image.load(images_directory + "background.jpg")
    pygame.display.set_icon(intersection_background)
    screen = pygame.display.set_mode((screen_width, screen_height))
    background = pygame.Surface(screen.get_size())
    background = background.convert(background)
    background.fill((250, 250, 250))
    pygame.init()
    font = pygame.font.SysFont('Arial', 20)
    pygame.display.set_caption('Car simulation')

    return screen, background, intersection_background, font


if __name__ == '__main__':
    from math import degrees, atan, pow, sqrt
    x1 = 382
    y1 = 385
    x2 = 435
    y2 = 435
    angle = (y2 - y1) / (x2 - x1)
    print(360 - degrees(atan(angle)))

