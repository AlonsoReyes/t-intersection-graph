import os
from math import pi, cos, sin, atan, ceil, sqrt, pow
from pygame import image, transform
from models.messages import *
from models.node import Node
from utils.utils import *

images_directory = os.path.dirname(os.path.abspath(__file__)) + "/../images/"


# Behaviour will be create a Channel and then add cars to it, when added the channel will send NewCarMessage
class Car(object):
    """
    Car representation. It has x and y position (as in a cartesian plane), an absolute speed and a direction. In case
    of movement, the total movement will be escalated into x and y with the direction.
    Also, the car has a fixed acceleration and maximum speed.
    """
    TIME_STEP = 0.1
    SPEED_FACTOR = 2
    max_forward_speed = 20.0  # meters/seconds.
    image_scale_rate = 0.05
    maximum_acceleration = 4.2
    minimum_acceleration = -5.0

    def __init__(self, name, pos_x=0.0, pos_y=0.0, absolute_speed=0.0, acceleration_rate=3.0, direction=0, lane=1,
                 creation_time=None, left_intersection_time=None, channel=None, intention="s", ticks=4,
                 coordination_ticks=4):
        """
        :param name: id to identify the car. Integer
        :param pos_x: x value of the car position.
        :param pos_y: y value of the car position.
        :param absolute_speed: absolute speed of the car.
        :param direction: direction of the car. Represented in degrees.
        :param lane: lane in which the car is travelling.
        :param direction: direction at which the front of the car is looking.
        :param controller: object which controls the speed of the car.
        """

        # Pygame variables
        self.image = None
        self.rotated_image = None
        self.screen_car = None

        # Basic parameters

        # The car identifier just to simplify things
        self.name = name

        # initial speed of the car when it appeared in the simulation.
        self.initial_speed = absolute_speed

        self.absolute_speed = absolute_speed

        # meters/seconds*seconds.
        self.acceleration_rate = acceleration_rate

        # What it intends to do, go straight, turn left or right. 's', 'l', 'r'
        self.intention = intention

        # Saves the position, direction and lane. The direction is in degrees. Where the car is pointing to.
        # The lane which the car enters the intersection, South: 0, East: 1, North: 2, West: 3
        self.initial_coordinates = {'pos_x': pos_x, 'pos_y': pos_y, 'direction': direction, 'lane': lane}
        self.actual_coordinates = {'pos_x': pos_x, 'pos_y': pos_y, 'direction': direction, 'lane': lane}

        # Follower variables
        # Dictionary that represents the caravan
        # It has to be a dictionary of Nodes because you need to store the follow list, the intention and
        # origin lane
        # key = id, value = Node(list of cars, intention, lane)
        self.graph = {}

        # List of ids, need to start checking from here when a new car is added
        # When a new car is added it may replace some of the leaves. The BFS search starts from this ids.
        self.leaf_cars = set()

        # Dictionary with the key being the id of the cars that I follow and the content
        # is the info I need to know about it. Current position, speed and acceleration
        self.following_cars = {}

        # Supervisor and second at charge id, needed to know that the messages sent from those
        # cars are the ones that I need to pay attention to.
        self.supervisor_car = None
        self.second_at_charge = None

        # Movement variables
        self.control_law_value = 0  # ?
        self.last_virtual_distance = 0  # ?

        # Time
        self.left_intersection_time = left_intersection_time  # ticks
        self.creation_time = creation_time  # ticks
        # Every time this amount of ticks passes the car broadcasts an InfoMessage
        self.update_ticks = ticks
        # Keeps count of the ticks that have passed
        self.counter = 0

        self.coordination_counter = 0
        self.coordination_ticks = coordination_ticks

        # Channel object, it is used to simulate a broadcast
        self.channel = channel

        if channel is not None:
            channel.add_car(self)
            self.broadcast(NewCarMessage(self))

        # TODO
        # Variables to simulate errors
        self.lie_to_supervisor = False

        # supervisor variables for attacks
        self.supervisor_lies = False
        self.supervisor_is_lying = False

    def __eq__(self, other):
        """
        compares two cars. For simplicity, two cars are the same if they share the same name
        :param other: other car
        :return: <boolean>
        """
        if isinstance(other, type(self)):
            if other.get_name() == self.get_name():
                return True
        return False

    def __str__(self):
        """
        String representation of the car. Adapted to output actual state of the car to a log file.
        Example: "Car: 48 Speed: 19.975 Following: 47" if car is following other car,
        Example: "Car: 48 Speed: 19.975" else.
        :return: String representation of the car.
        """
        return "Car " + str(self.get_name()) + " lane " + str(self.get_lane()) + " intention " + self.get_intention() \
               + " follows + " + ''.join([str(car) for car in self.get_following_cars()]) \
               + " creation time " + str(self.get_creation_time())

    # Getters and Setters
    def get_name(self):
        """
        :return: returns the id of the car
        """
        return self.name

    def set_name(self, new_name):
        """
        :param new_name: an int representing the id of the car
        """
        self.name = new_name

    # Coordinates and position getters and setters
    def get_lane(self):
        """
        :return: returns and int representing the lane of the car
        """
        return self.actual_coordinates['lane']

    def set_lane(self, new_lane):
        """
        :param new_lane: int representing the new lane of the car
        """
        self.actual_coordinates['lane'] = new_lane

    def get_intention(self):
        """
        :return: char representing what the car is going to do. Go straight ('s'), turn right or left ('r' or 'l')
        """
        return self.intention

    def set_intention(self, new_intention):
        if new_intention in ['s', 'l', 'r']:
            self.intention = new_intention

    def get_direction(self):
        return self.actual_coordinates['direction']

    def set_direction(self, new_direction):
        self.actual_coordinates['direction'] = new_direction

    def get_x_coordinate(self):
        return self.actual_coordinates['pos_x']

    def set_x_coordinate(self, new_x):
        self.actual_coordinates['pos_x'] = new_x

    def get_y_coordinate(self):
        return self.actual_coordinates['pos_y']

    def set_y_coordinate(self, new_y):
        self.actual_coordinates['pos_y'] = new_y

    def get_position(self):
        return self.get_x_coordinate(), self.get_y_coordinate()

    def get_actual_coordinates(self):
        """
        Return the tuple containing the actual coordinates fo a car.
        :return: (<int>, <int>, <int>, <int>) actual coordinates of a car.
        """
        return self.actual_coordinates

    def get_origin_coordinates(self):
        """
        Return the tuple containing the origin coordinates fo a car.
        :return: (<int>, <int>, <int>, <int>) origin coordinates of a car.
        """
        return self.initial_coordinates

    # Speed
    def get_speed(self):
        return self.absolute_speed

    def set_speed(self, new_speed):
        self.absolute_speed = new_speed

    def get_acceleration(self):
        return self.acceleration_rate

    def set_acceleration(self, new_acceleration):
        """
        Follows restriction of the maximum and minimum rate established
        :param new_acceleration: float representing new acceleration rate
        """
        if new_acceleration < self.minimum_acceleration:
            new_acceleration = self.minimum_acceleration
        elif new_acceleration > self.maximum_acceleration:
            new_acceleration = self.maximum_acceleration
        self.acceleration_rate = new_acceleration

    # Coordination methods involving the graph and the followed cars
    def get_graph(self):
        return self.graph

    def set_graph(self, graph):
        self.graph = graph

    def get_following_cars(self):
        return self.following_cars

    def set_following_cars(self, new_dict_of_cars):
        """
        :param new_dict_of_cars: dictionary where the key is the id and the value is another dictionary with
        the speed, acceleration and position of the cars.
        :return:
        """
        self.following_cars = new_dict_of_cars

    def get_leaf_cars(self):
        """
        :return: returns list of ids that
        """
        return self.leaf_cars

    def set_leaf_cars(self, new_set):
        self.leaf_cars = new_set

    def add_leaf(self, car):
        self.leaf_cars.add(car)

    def remove_leaf(self, car):
        self.leaf_cars.remove(car)

    # Supervisor related
    def get_supervisor_car(self):
        return self.supervisor_car

    def set_supervisor_car(self, new_supervisor):
        self.supervisor_car = new_supervisor

    def get_second_at_charge(self):
        return self.second_at_charge

    def set_second_at_charge(self, new_second):
        self.second_at_charge = new_second

    def is_following(self):
        if not self.following_cars:
            return False
        else:
            return True

    def get_creation_time(self):
        return self.creation_time

    def set_creation_time(self, creation_time):
        self.creation_time = creation_time

    def get_update_ticks(self):
        return self.update_ticks

    def set_update_ticks(self, ticks):
        self.update_ticks = ticks

    # Visualization
    def get_image_scale_rate(self):
        return self.image_scale_rate

    def set_image_scale_rate(self, new_rate):
        self.image_scale_rate = new_rate

    # Visualization methods

    def get_rect(self):
        """
        Returns the rectangle which represents the car.
        :return: rectangle of the car
        """
        return self.screen_car

    def get_car_length(self):
        """
        Get the length of the car based on it's screen representation.
        :return: <int> length of a car.
        """
        return abs((self.get_rect().right - self.get_rect().left) * sin(self.get_direction() * pi / 180) +
                   (self.get_rect().top - self.get_rect().bottom) * cos(self.get_direction() * pi / 180))

    def new_image(self, scale_rate=image_scale_rate):
        """
        Creates the image representation of a car, with his rotated image and his screen representation (with the rect).
        """
        self.image = image.load(images_directory + "car.png")
        self.rotated_image = transform.rotate(self.image, self.get_direction())  # image of the car rotated
        self.rotated_image = transform.scale(self.rotated_image, (  # reduction of the size of the image
            int(self.rotated_image.get_rect().w * scale_rate),
            int(self.rotated_image.get_rect().h * scale_rate)))
        self.screen_car = self.rotated_image.get_rect()  # rectangle representation of the car
        self.screen_car.center = self.get_position()  # add the position to the rectangle

    def draw_car(self):
        """
        Prepares the image of the car to be drawn. The image is rotated, re-escalated and moved.
        """
        self.rotated_image = transform.rotate(self.image, self.get_direction())
        self.rotated_image = transform.scale(self.rotated_image, (
            int(self.rotated_image.get_rect().w * self.get_image_scale_rate()),
            int(self.rotated_image.get_rect().h * self.get_image_scale_rate())))
        self.screen_car = self.rotated_image.get_rect()
        self.screen_car.center = self.get_position()

    # Movement methods

    def check_collision(self, other_car):
        """
        :param other_car: object of type Car
        :return: boolean representing if the cars collide
        """
        return self.get_rect().colliderect(other_car.get_rect())

    def cross_path(self, other_car_lane, other_car_intention):
        """
        Check if the path of one car crosses tih the path o f another. It is true if the other car is the same lane
        or if the other car is in one of the perpendicular lanes.
        :param other_car_intention: the intention of way of the other car
        :param other_car_lane: the lane at which the other car star its way.
        :return: True if the paths does not crosses, False otherwise.
        """
        self_lane = self.get_lane()
        self_intention = self.get_intention()
        lane_to_int_dict = {"l": 0, "s": 1, "r": 2}
        table0 = [[True, True, True], [True, True, True], [True, True, True]]
        table1 = [[True, True, False], [True, True, False], [False, True, False]]
        table2 = [[True, True, True], [True, False, False], [True, False, False]]
        table3 = [[True, True, False], [True, True, True], [False, False, False]]
        all_tables = [table0, table1, table2, table3]
        return all_tables[(self_lane - other_car_lane) % 4][lane_to_int_dict[self_intention]][
            lane_to_int_dict[other_car_intention]]

    def accelerate(self):
        """
        Function to accelerate a car. Exception raised if maximum speed is reached or surpassed. Time unit is necessary
         to work in milliseconds. Seconds = 1000.
        :return: None
        """
        speed_diff = self.acceleration_rate * self.TIME_STEP
        new_speed = self.absolute_speed + speed_diff

        if new_speed > self.max_forward_speed:
            self.absolute_speed = self.max_forward_speed
        elif new_speed < 0:
            self.absolute_speed = 0
        else:
            self.absolute_speed = new_speed

    # Graph methods
    # adds then new car to the graph with its follow list, it doesnt add the follow list which contains the
    # important data of the cars, it gets this when they send an info message
    def add_new_car(self, name, lane, intention):
        graph = self.get_graph()
        leaf_cars = self.get_leaf_cars()
        follow_list = list()
        visited = set()
        # list of nodes
        to_visit = [graph[car] for car in leaf_cars]
        # starts checking the leaves
        while to_visit:
            node = to_visit.pop(0)
            if node.get_name() not in visited:
                visited.add(node.get_name())
                if cars_cross_path(lane, intention, node.get_lane(), node.get_intention()):
                    # print(self.get_name(), ' ', name)
                    follow_list.append(node.get_name())
                    for car in node.get_follow_list():
                        visited.add(car)
                else:
                    # If it doesn't collide then add the follow list of the node to to_visit list
                    to_visit = to_visit + [graph[car] for car in graph[node.get_name()].get_follow_list()]

        for car in follow_list:
            if car in self.get_leaf_cars():
                leaf_cars.remove(car)
        leaf_cars.add(name)
        if name == self.get_name() and name in follow_list:
            follow_list.remove(name)
        graph[name] = Node(name=name, follow_list=follow_list, lane=lane, intention=intention)
        return follow_list

    # Methods to receive messages
    # Message methods
    def broadcast(self, message):
        self.channel.broadcast(message)

    def get_coordination_counter(self):
        return self.coordination_counter

    def set_coordination_counter(self, count):
        self.coordination_counter = count

    def add_to_coordination_counter(self, number):
        self.coordination_counter += number

    def get_coordination_ticks(self):
        return self.coordination_ticks

    def get_counter(self):
        return self.counter

    def set_counter(self, new_count):
        self.counter = new_count

    def add_to_counter(self, number):
        self.counter += number

    def send_info_message(self):
        self.broadcast(InfoMessage(self))

    def send_left_intersection_message(self):
        self.broadcast(LeftIntersectionMessage(self))

    def receive_info_message(self, message):
        if message.get_sender_name() in self.following_cars:
            followed = self.following_cars[message.get_sender_name()]
            x, y = message.get_sender_position()
            followed['pos_x'] = x
            followed['pos_y'] = y
            followed['speed'] = message.get_sender_speed()
            followed['direction'] = message.get_sender_direction()
            followed['acceleration'] = message.get_sender_acceleration()
            # Maybe do something here or in the update method with this info

    def receive_new_car_message(self, message):
        if message.get_sender_name() not in self.get_graph():
            name = message.get_sender_name()
            lane = message.get_sender_lane()
            intention = message.get_sender_intention()
            self.add_new_car(name=name, lane=lane, intention=intention)

    def receive_left_intersection_message(self, message):
        sender_name = message.get_sender_name()
        if sender_name in self.following_cars:
            del self.following_cars[sender_name]
        del self.graph[sender_name]

    def receive_welcome_message(self, message):
        if self.get_name() == message.get_receiver_name() or \
                self.supervisor_car is None:
            self.set_supervisor_car(message.get_supervisor())
            self.set_second_at_charge(message.get_second_at_charge())
            self.set_following_cars(message.get_follow_list())
            self.set_graph(message.get_graph())

    def receive_second_at_charge_message(self, message):
        if message.get_receiver_name() == self.get_name():
            self.set_second_at_charge(self.get_name())
            self.__class__ = SecondAtChargeCar

    def receive_message(self, message):
        if message.is_info_message():
            self.receive_info_message(message)

        elif message.is_left_intersection_message():
            self.receive_left_intersection_message(message)

        elif message.is_welcome_message():
            self.receive_welcome_message(message)

        elif message.is_new_car_message():
            self.receive_new_car_message(message)

        elif message.is_second_at_charge_message():
            self.receive_second_at_charge_message(message)

    def choose_second_at_charge(self):
        key_list = sorted(self.get_graph().keys())
        res = None
        for i, v in enumerate(key_list):
            if v == self.get_name() and i < len(key_list):
                res = self.get_graph()[key_list[i + 1]].get_name()
                break
        return res

    def check_coordination(self):
        # +1 to avoid 0%something, avoids doing it at the beginning
        if (self.get_coordination_counter() + 1) % (self.get_coordination_ticks() + 1) == 0 \
                and self.get_supervisor_car() is None:
            self.__class__ = SupervisorCar
            self.supervisor_car = self.get_name()
            self.set_coordination_counter(0)
            self.set_second_at_charge(self.choose_second_at_charge())
            self.broadcast(WelcomeMessage(self))
        self.add_to_coordination_counter(1)

    def send_update(self):
        # +1 to avoid 0%something, avoids doing it at the beginning
        if (self.get_counter() + 1) % (self.get_update_ticks() + 1) == 0:
            self.send_info_message()

    def update(self):
        self.send_update()
        self.check_coordination()
        self.add_to_counter(1)

    # Check type
    def is_supervisor(self):
        return False

    def is_second_at_charge(self):
        return False

    def test_method(self):
        self.__class__ = SupervisorCar
        return self.is_supervisor()


# TODO REMEMBER TO CHANGE RECEIVE NEW CAR MESSAGE, NEEDS TO SEND MESSAGES BACK AS SUPERVISOR
class SupervisorCar(Car):

    def test_method(self):
        print("SupervisorCar")

    def is_supervisor(self):
        return True

    def send_welcome_message(self, receiver_name=None):
        self.broadcast(WelcomeMessage(sender_car=self, receiver_name=receiver_name))

    def receive_new_car_message(self, message):
        if message.get_sender_name() not in self.get_graph():
            name = message.get_sender_name()
            lane = message.get_sender_lane()
            intention = message.get_sender_intention()
            self.add_new_car(name=name, lane=lane, intention=intention)
            self.broadcast(WelcomeMessage(sender_car=self, receiver_name=message.get_sender_name()))


class SecondAtChargeCar(Car):

    def is_second_at_charge(self):
        return True
