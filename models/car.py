import os
import pygame
from math import pi, cos, sin
from pygame import image, transform
from models.messages import *
from models.node import Node
import copy

images_directory = os.path.dirname(os.path.abspath(__file__)) + "/../images/"


# Behaviour will be create a Channel and then add cars to it
# Cars will spawn outside the graphic area, so they won't send a new car message when created.
# When they enter the area they will call the method enter_intersection and then they will send the
# NewCarMessage and add themselves to the Channel list of cars. This is to simulate entering the coop zone.
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
    maximum_acceleration = 5.0  # 4.2
    minimum_acceleration = -5.0  # -5.0

    def __init__(self, name, pos_x=0.0, pos_y=0.0, absolute_speed=0.0, acceleration_rate=3.0, direction=0, lane=1,
                 creation_time=None, left_intersection_time=None, channel=None, intention="s", ticks=1,
                 coordination_ticks=2, graph=None, leaf_cars=None, inner_intersection=None, full_intersection=None,
                 controller=None, sensor_flag=False):
        """
        :param name: id to identify the car. Integer
        :param pos_x: x value of the car position.
        :param pos_y: y value of the car position.
        :param absolute_speed: absolute speed of the car.
        :param direction: direction of the car. Represented in degrees.
        :param lane: lane in which the car is travelling.
        :param direction: direction at which the front of the car is looking.
        """

        # Visualization variables
        self.image = None
        self.rotated_image = None
        self.screen_car = None

        # Basic parameters

        # Intersection rectangle. Used to check when the car enters the coop zone
        self.full_intersection_rectangle = full_intersection
        self.inner_intersection_rectangle = inner_intersection
        self.inside_full_rectangle = False
        self.left_inner_rectangle = False
        self.last_to_leave = False

        # The car identifier just to simplify things
        self.name = name

        # initial speed of the car when it appeared in the simulation.
        self.initial_speed = absolute_speed

        self.absolute_speed = absolute_speed

        # meters/seconds*seconds.
        self.initial_acceleration = acceleration_rate
        self.acceleration_rate = acceleration_rate

        # What it intends to do, go straight, turn left or right. 's', 'l', 'r'
        self.intention = intention

        # Saves the position, direction and lane. The direction is in degrees. Where the car is pointing to.
        # The lane which the car enters the intersection, South: 0, East: 1, North: 2, West: 3
        self.initial_coordinates = {'pos_x': pos_x, 'pos_y': pos_y, 'direction': direction, 'lane': lane}
        self.actual_coordinates = {'pos_x': pos_x, 'pos_y': pos_y, 'direction': direction, 'lane': lane}

        # Function that takes care of the cars movement
        self.controller = controller

        # Follower variables
        # Dictionary that represents the caravan
        # It has to be a dictionary of Nodes because you need to store the follow list, the intention and
        # origin lane
        # key = id, value = Node(list of cars, intention, lane)
        self.graph = graph
        if graph is None:
            self.graph = {}

        # List of ids, need to start checking from here when a new car is added
        # When a new car is added it may replace some of the leaves. The BFS search starts from this ids.
        self.leaf_cars = leaf_cars
        if leaf_cars is None:
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
        # Doubting this things due to the system that works in base of rounds
        self.left_intersection_time = left_intersection_time  # ticks
        self.creation_time = creation_time  # ticks
        # Every time this amount of ticks passes the car broadcasts an InfoMessage
        self.update_ticks = ticks
        # Keeps count of the ticks that have passed
        self.counter = 1

        self.coordination_counter = 1
        self.coordination_ticks = coordination_ticks

        # Channel object, it is used to simulate a broadcast
        self.channel = channel

        # Messages follow a round system, but when a car enters the intersection it's message
        # needs to be sent immediately, otherwise it will be send at the start of the next round
        # and at that time the car needs to be coordinated already
        # if channel is not None:
        #     channel.add_car(self)
        #     self.send_new_car_message()

        # TODO
        # Variables to simulate errors
        self.lie_to_supervisor = False

        # supervisor variables for attacks
        self.supervisor_lies = False
        self.supervisor_is_lying = False

        # Sets the rectangle that represents the car in pygame
        self.new_image()
        # It takes care of the movement of the car so it doesn't crash with the car in front of it in the same lane
        self.sensor = None
        if sensor_flag:
            self.init_sensor()
        # Sets the car as the last car to enter through that lane
        channel.last_to_enter_notification(self)

    def init_sensor(self):
        from utils.utils import create_sensor
        self.sensor = create_sensor(owner_car=self)

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
    def get_time_step(self):
        return self.TIME_STEP

    def set_time_step(self, time_step):
        self.TIME_STEP = time_step

    def get_speed_factor(self):
        return self.SPEED_FACTOR

    def set_speed_factor(self, speed_factor):
        self.SPEED_FACTOR = speed_factor

    def get_sensor(self):
        return self.sensor

    def set_sensor(self, sensor):
        self.sensor = sensor

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

    def get_origin_direction(self):
        return self.initial_coordinates['direction']

    def get_x_coordinate(self):
        return self.actual_coordinates['pos_x']

    def set_x_coordinate(self, new_x):
        self.actual_coordinates['pos_x'] = new_x

    def get_origin_x_coordinate(self):
        return self.initial_coordinates['pos_x']

    def get_y_coordinate(self):
        return self.actual_coordinates['pos_y']

    def set_y_coordinate(self, new_y):
        self.actual_coordinates['pos_y'] = new_y

    def get_origin_y_coordinate(self):
        return self.initial_coordinates['pos_y']

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

    def get_initial_speed(self):
        return self.initial_speed

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

    def get_origin_acceleration(self):
        return self.initial_acceleration

    def get_inside_full_rectangle(self):
        return self.inside_full_rectangle

    def set_inside_full_rectangle(self, inside):
        self.inside_full_rectangle = inside

    # Coordination methods involving the graph and the followed cars
    def get_graph(self):
        return self.graph

    def set_graph(self, graph):
        self.graph = copy.deepcopy(graph)

    def get_following_cars(self):
        return self.following_cars

    def set_following_cars(self, new_dict_of_cars):
        """
        :param new_dict_of_cars: dictionary where the key is the id and the value is another dictionary with
        the speed, acceleration and position of the cars.
        :return:
        """
        self.following_cars = copy.deepcopy(new_dict_of_cars)

    def get_leaf_cars(self):
        """
        :return: returns list of ids that
        """
        return self.leaf_cars

    def set_leaf_cars(self, new_set):
        self.leaf_cars = copy.deepcopy(new_set)

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

    def get_controller(self):
        return self.controller

    def set_controller(self, controller):
        self.controller = controller

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
    def inside_inner_intersection(self):
        """
        Checks if the car entered the collision area
        :return: boolean which represents if the car entered the inner rectangle
        """
        return self.get_rect().colliderect(self.inner_intersection_rectangle)

    def inside_full_intersection(self):
        """
        Checks if the car entered the screen
        :return: boolean which represents if the car entered the screen rectangle
        """
        return self.get_rect().colliderect(self.full_intersection_rectangle)

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

    def move(self):
        """
        Function to move a car. If its speed its 0, it'll not move. Time unit is necessary to work in milliseconds.
        Seconds = 1000.
        """
        rad = self.get_direction() * pi / 180
        pos_x = self.get_x_coordinate()
        pos_y = self.get_y_coordinate()
        pos_x_diff = -sin(rad) * self.get_speed() * self.TIME_STEP * self.SPEED_FACTOR
        pos_y_diff = -cos(rad) * self.get_speed() * self.TIME_STEP * self.SPEED_FACTOR
        self.set_x_coordinate(pos_x + pos_x_diff)
        self.set_y_coordinate(pos_y + pos_y_diff)

    # Graph methods
    # adds then new car to the graph with its follow list, it doesnt add the follow list which contains the
    # important data of the cars, it gets this when they send an info message
    def add_new_car(self, name, lane, intention):
        from utils.utils import cars_cross_path
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

    def send_welcome_message(self, receiver_name=None):
        self.broadcast(WelcomeMessage(sender_car=self, receiver_name=receiver_name))

    def send_second_at_charge_message(self, receiver_name=None):
        self.broadcast(SecondAtChargeMessage(sender_car=self, receiver_name=receiver_name))

    def send_new_car_message(self):
        # self.add_message(NewCarMessage(self))
        self.broadcast(NewCarMessage(self))

    # Returns the lane that the car will end up in
    def destination_lane(self):
        destination = None
        lane = self.get_lane()
        if lane == 0:
            if self.intention == 's':
                destination = 2
            elif self.intention == 'l':
                destination = 3
            elif self.intention == 'r':
                destination = 1
        elif lane == 1:
            if self.intention == 's':
                destination = 3
            elif self.intention == 'l':
                destination = 0
            elif self.intention == 'r':
                destination = 2
        elif lane == 2:
            if self.intention == 's':
                destination = 0
            elif self.intention == 'l':
                destination = 1
            elif self.intention == 'r':
                destination = 3
        elif lane == 3:
            if self.intention == 's':
                destination = 1
            elif self.intention == 'l':
                destination = 2
            elif self.intention == 'r':
                destination = 0
        return destination

    # Checks if the car left the inner intersection rectangle and sends a LeaveIntersectionMessage
    # rectangle size (280, 280, 210, 210)
    def check_left_inner_intersection(self):
        left = False
        destination = self.destination_lane()
        pos_x, pos_y = self.get_position()
        car_length = self.get_car_length() / 2.0
        inner_rect_width = self.inner_intersection_rectangle.w
        inner_rect_height = self.inner_intersection_rectangle.h
        inner_rect_left = self.inner_intersection_rectangle.left
        inner_rect_top = self.inner_intersection_rectangle.top
        if destination == 0:
            if pos_y - car_length > inner_rect_top + inner_rect_height:
                left = True
        elif destination == 1:
            if pos_x - car_length > inner_rect_left + inner_rect_width:
                left = True
        elif destination == 2:
            if pos_y + car_length < inner_rect_top:
                left = True
        elif destination == 3:
            if pos_x + car_length < inner_rect_left:
                left = True
        return left and not self.inside_inner_intersection()

    # Checks the position of the car so it sends the NewCarMessage when it enters the coop zone and
    # sends the LeaveIntersectionMessage when it leaves the inner rectangle
    def check_position(self):
        if self.full_intersection_rectangle is not None and self.inner_intersection_rectangle is not None:
            # If it hasn't changed to being inside the rectangle but it is colliding
            if not self.inside_full_rectangle and self.inside_full_intersection():
                self.enter_intersection()
            if self.inside_full_rectangle:
                if not self.left_inner_rectangle and self.check_left_inner_intersection():
                    self.leave_inner_intersection()
            # If a bit of the car left the inner intersection it has to be assigned as the last one to leave
            if not self.last_to_leave and self.inner_intersection_rectangle.contains(self.screen_car):
                self.last_to_leave = True
                self.channel.last_to_leave_notification(self)

    # Changes the state of the car to represent that it entered the coop zone, adds itself to the channel and
    # sends a NewCarMessage
    def enter_intersection(self):
        self.inside_full_rectangle = True
        self.channel.add_car(self)
        self.send_new_car_message()

    # To add more info you need to add it here and to the prepare_follow_list function in utils.
    def receive_info_message(self, message):
        # print("InfoMessage \nSender: ", message.get_sender_name(), " Receiver: ", self.get_name())
        if message.get_sender_name() in self.following_cars:
            followed = self.following_cars[message.get_sender_name()]
            x, y = message.get_sender_position()
            followed['pos_x'] = x
            followed['pos_y'] = y
            followed['speed'] = message.get_sender_speed()
            followed['direction'] = message.get_sender_direction()
            followed['acceleration'] = message.get_sender_acceleration()
            followed['intention'] = message.get_sender_intention()
            followed['lane'] = message.get_sender_lane()
            # Maybe do something here or in the update method with this info

    def receive_new_car_message(self, message):
        # print("NewCarMessage \nSender: ", message.get_sender_name(), " Receiver: ", self.get_name())
        if message.get_sender_name() not in self.get_graph():
            name = message.get_sender_name()
            lane = message.get_sender_lane()
            intention = message.get_sender_intention()
            self.add_new_car(name=name, lane=lane, intention=intention)

    # It simply deletes from the lists and dictionaries
    def receive_left_intersection_message(self, message):
        # print("LeftIntersectionMessage \nSender: ", message.get_sender_name(), " Receiver: ", self.get_name())
        sender_name = message.get_sender_name()
        if sender_name == self.get_supervisor_car():
            self.set_supervisor_car(self.get_second_at_charge())
            self.set_second_at_charge(None)
        if sender_name == self.get_second_at_charge():
            self.set_second_at_charge(None)
        if sender_name in self.get_following_cars():
            del self.get_following_cars()[sender_name]
        if sender_name in self.get_leaf_cars():
            self.get_leaf_cars().remove(sender_name)
        # Prevents the case where the car leaves before a car that entered the coop zone is coordinated.
        # In that case the car won't have the leaving car in it's graph
        # Shouldn't happen because of the way messages are handled
        if sender_name in self.get_graph():
            del self.get_graph()[sender_name]
        # Removes the car from the follow lists in the graph. Keeps graph info updated
        for node in self.get_graph().values():
            follow_list = node.get_follow_list()
            if sender_name in follow_list:
                follow_list.remove(sender_name)

    # If the supervisor car is None is the base case.
    def receive_welcome_message(self, message):
        # print("WelcomeMessage \nSender: ", message.get_sender_name(), " Receiver: ", self.get_name(),
        #       " Destination: ", message.get_receiver_name())
        if self.get_name() == message.get_receiver_name() or \
                self.get_supervisor_car() is None:
            self.set_supervisor_car(message.get_supervisor())
            self.set_second_at_charge(message.get_second_at_charge())
            # gets the prepared list from the welcome message using its name
            # needed like this later to be able to receive InfoMessages correctly
            self.set_leaf_cars(message.get_leaf_cars())
            self.set_following_cars(message.get_follow_list(self.get_name()))
            self.set_graph(copy.deepcopy(message.get_graph()))

    # Every car sets the second at charge and the car that is meant to receive it sets the supervisor car too.
    # That is done just to work with how the messages are received
    def receive_second_at_charge_message(self, message):
        # print("SecondAtChargeMessage \nSender: ", message.get_sender_name(), "Receiver: ", self.get_name(),
        #      " Destination: ", message.get_receiver_name())
        """
        if message.get_sender_name() == self.get_second_at_charge():
            self.set_supervisor_car(self.second_at_charge)
            self.set_second_at_charge(message.get_receiver_name())
        """
        if message.get_sender_name() == self.get_supervisor_car():
            self.set_second_at_charge(message.get_receiver_name())
            if message.get_receiver_name() == self.get_name():
                self.__class__ = SecondAtChargeCar

    # Just a method that acts as a switch case to process the messages
    # No double dispatch or elegant way implemented because in reality the car will process
    # it's messages.
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

    # Chooses the second at charge as the one that joined next
    # This is done by sorting the dictionary keys of the graph
    # To choose it differently you need to change this method
    def choose_second_at_charge(self):
        key_list = sorted(self.get_graph().keys())
        res = None
        for i, v in enumerate(key_list):
            if v == self.get_supervisor_car() and i < key_list.index(max(key_list)):
                res = self.get_graph()[key_list[i + 1]].get_name()
                break
        return res

    # It is important that the welcome message is sent first because otherwise
    # the car that is receiving will already be the second in charge and will have
    # the supervisor set correctly but no graph.
    def check_coordination(self):
        self.add_to_coordination_counter(1)
        if self.get_coordination_counter() % self.get_coordination_ticks() == 0 \
                and self.get_supervisor_car() is None:
            self.__class__ = SupervisorCar
            self.supervisor_car = self.get_name()
            self.set_coordination_counter(0)
            self.set_second_at_charge(self.choose_second_at_charge())
            # Important
            self.send_welcome_message()
            second = self.get_second_at_charge()
            if second is not None:
                self.send_second_at_charge_message(self.get_second_at_charge())

    # Every time the amount set as update_ticks passes the car sends an InfoMessage
    # so the cars following it get information about it
    def send_update(self):
        if self.get_counter() % self.get_update_ticks() == 0:
            self.send_info_message()

    def leave_inner_intersection(self):
        self.left_inner_rectangle = True
        self.send_left_intersection_message()
        self.channel = None

    def get_virtual_x_position(self):
        """
        Returns the x position of the virtual caravan environment.
        :return: <float> x position at the virtual environment
        """
        rad = self.get_origin_direction() * pi / 180
        x_real = (self.get_x_coordinate() - self.get_origin_x_coordinate()) * sin(rad)
        y_real = (self.get_y_coordinate() - self.get_origin_y_coordinate()) * cos(rad)
        return abs(x_real + y_real)

    def get_virtual_y_position(self):
        """
        Returns the x position of the virtual caravan environment.
        :return: <float> x position at the virtual environment
        """
        rad = self.get_origin_direction() * pi / 180
        x_real = - 1 * (self.get_x_coordinate() - self.get_origin_x_coordinate()) * cos(rad)
        y_real = (self.get_y_coordinate() - self.get_origin_y_coordinate()) * sin(rad)
        return x_real + y_real

    def distance_to_inner_intersection(self):
        lane = self.get_lane()
        inner_rectangle = self.inner_intersection_rectangle
        top = inner_rectangle.top
        left = inner_rectangle.left
        height = inner_rectangle.h
        width = inner_rectangle.w
        distance = 0
        if lane == 0:
            distance = self.get_y_coordinate() - (top + height)
        elif lane == 1:
            distance = self.get_x_coordinate() - (left + width)
        elif lane == 2:
            distance = top - self.get_y_coordinate()
        elif lane == 3:
            distance = left - self.get_x_coordinate()
        return distance

    # It turns the car to the right or left lane exactly
    def turn_direction(self, radio, degrees=90):
        direction_change = degrees * (self.get_speed() * self.TIME_STEP * self.SPEED_FACTOR) / (
                pi / 2 * radio)
        if self.get_intention() == 'r':
            self.set_direction(self.get_direction() - direction_change)
        else:
            self.set_direction(self.get_direction() + direction_change)

    def correct_direction(self, degrees=90):
        actual_direction = self.get_direction()
        if self.get_intention() == 'l':
            target_direction = (self.get_origin_direction() + degrees) % 360
            cmp = abs(target_direction - abs(actual_direction))
            if cmp != 0.0 and cmp < 2.0:
                self.set_direction(target_direction)
        else:
            target_direction = abs(360 - self.get_origin_direction() - degrees) % 360
            cmp = abs(target_direction - abs((360 - abs(actual_direction))))
            if cmp != 0.0 and cmp < 2.0:
                self.set_direction(target_direction)

    def turn(self):
        """
        Turns the car to the direction it intends to turn.
        """
        from utils.utils import get_right_turn_radio, get_left_turn_radio
        if self.inner_intersection_rectangle is not None \
                and self.full_intersection_rectangle is not None:
            extra_distance = 0
            right_turn_radio = get_right_turn_radio(self.get_lane())
            left_turn_radio = get_left_turn_radio(self.get_lane(), extra_distance=extra_distance)
            if self.get_intention() == "r":
                if self.get_virtual_y_position() > -right_turn_radio and \
                        self.distance_to_inner_intersection() <= 0:
                    self.turn_direction(radio=right_turn_radio)
            elif self.get_intention() == "l":
                if self.get_virtual_y_position() < left_turn_radio and \
                        self.distance_to_inner_intersection() + extra_distance <= 0:
                    self.turn_direction(radio=left_turn_radio)
            self.correct_direction()

    def move_control(self):
        self.accelerate()
        self.turn()
        self.move()
        self.draw_car()

    # Minimum process to simulate the coordination system
    # TODO: ADD THE MOVEMENT PART TO SIMULATE A TICK AND MAKE CONTROLLER THAT USES THE INFO FROM THE CARS
    def update(self):
        if self.get_controller() is not None:
            self.get_controller()(self)

        if self.sensor is not None:
            self.sensor.watch()

        self.move_control()
        self.check_position()

        if self.inside_full_rectangle and not self.left_inner_rectangle:
            self.send_update()
            if self.supervisor_car is None:
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

    def delete_self(self):
        del self.get_graph()[self.get_name()]


class SupervisorCar(Car):

    def test_method(self):
        print("SupervisorCar")

    def is_supervisor(self):
        return True

    def receive_new_car_message(self, message):
        # print("NewCarMessageSupervisor\nSender: ", message.get_sender_name(), " Receiver: ", self.get_name())
        if message.get_sender_name() not in self.get_graph():
            name = message.get_sender_name()
            lane = message.get_sender_lane()
            intention = message.get_sender_intention()
            self.add_new_car(name=name, lane=lane, intention=intention)
            if self.get_second_at_charge() is None:
                self.set_second_at_charge(name)
                self.send_second_at_charge_message(receiver_name=name)
            self.send_welcome_message(receiver_name=message.get_sender_name())

    # Adds the case where the second at charge leaves before the supervisor, not gonna happen.
    def receive_left_intersection_message(self, message):
        # print("LeftIntersectionMessageSupervisor \nSender: ", message.get_sender_name(), \
        #  " Receiver: ", self.get_name())
        # This is because in the method from the super class it sets second at charge to None if it is the one
        # that sends the message, so the supervisor needs to know who it was before it changes it
        current_second = self.get_second_at_charge()
        super(SupervisorCar, self).receive_left_intersection_message(message)
        if message.get_sender_name() == current_second:
            second = self.choose_second_at_charge()
            self.set_second_at_charge(second)
            self.send_second_at_charge_message(second)


class SecondAtChargeCar(Car):

    def is_second_at_charge(self):
        return True

    def receive_left_intersection_message(self, message):
        # print("LeftIntersectionMessageSecond \nSender: ", message.get_sender_name(), " Receiver: ", self.get_name())
        sender_name = message.get_sender_name()
        if sender_name in self.get_following_cars():
            del self.get_following_cars()[sender_name]
        if sender_name in self.get_leaf_cars():
            self.get_leaf_cars().remove(sender_name)
        del self.get_graph()[sender_name]
        if sender_name != self.get_name() and sender_name == self.get_supervisor_car():
            self.set_supervisor_car(self.get_name())
            self.__class__ = SupervisorCar
            second = self.choose_second_at_charge()
            self.set_second_at_charge(second)
            # print("SecondAtChargemsg: Sender ", sender_name, " Receiver: ", self.get_name(), " New:", second)
            self.send_second_at_charge_message(second)


class SimulationCar(Car):

    def __init__(self, car=None, name=None, pos_x=0, pos_y=0, absolute_speed=0, acceleration_rate=0, direction=0,
                 lane=0, intention='s', inner_intersection=None, full_intersection=None):
        if car is not None:
            name = car.get_name()
            pos_x = car.get_x_coordinate()
            pos_y = car.get_y_coordinate()
            absolute_speed = car.get_speed()
            acceleration_rate = car.get_acceleration()
            direction = car.get_direction()
            lane = car.get_lane()
            intention = car.get_intention()
            inner_intersection = car.inner_intersection_rectangle
            full_intersection = car.full_intersection_rectangle
        super(SimulationCar, self).__init__(name=name, pos_x=pos_x,
                                            pos_y=pos_y, absolute_speed=absolute_speed,
                                            acceleration_rate=acceleration_rate,
                                            direction=direction, lane=lane,
                                            intention=intention,
                                            inner_intersection=inner_intersection,
                                            full_intersection=full_intersection)
        self.previous_direction = direction
        self.previous_speed = absolute_speed
        self.previous_acceleration = acceleration_rate
        self.previous_x = pos_x
        self.previous_y = pos_y

    def reset(self):
        self.set_x_coordinate(self.get_origin_x_coordinate())
        self.set_y_coordinate(self.get_origin_y_coordinate())
        self.set_speed(self.get_initial_speed())
        self.set_direction(self.get_origin_direction())
        self.set_acceleration(self.get_origin_acceleration())
        self.draw_car()

    def save_state(self):
        self.previous_x = self.get_x_coordinate()
        self.previous_y = self.get_y_coordinate()
        self.previous_acceleration = self.get_acceleration()
        self.previous_direction = self.get_direction()
        self.previous_speed = self.get_speed()

    def reverse(self):
        self.set_x_coordinate(self.previous_x)
        self.set_y_coordinate(self.previous_y)
        self.set_speed(self.previous_speed)
        self.set_direction(self.previous_direction)
        self.set_acceleration(self.previous_acceleration)
        self.draw_car()

    def update(self):
        self.move_control()

    def check_if_passed(self, point_x, point_y, point=None):
        from utils.utils import get_distance
        passed = False
        pos_x, pos_y = self.get_position()
        if point is None:
            point = pygame.Rect(point_x, point_y, 1, 1)
        self.save_state()
        before_distance = get_distance(pos_x, pos_y, point_x, point_y)
        self.move_control()
        pos_x, pos_y = self.get_position()
        after_distance = get_distance(pos_x, pos_y, point_x, point_y)
        self.reverse()
        if after_distance > before_distance and not self.screen_car.colliderect(point):
            passed = True
        return passed

    def collision_with_point(self, collision_x, collision_y):
        point = pygame.Rect(collision_x, collision_y, 1, 1)
        return self.screen_car.colliderect(point)

    # return value is -1 if the car already passed that point and is not touching it
    # Returns the amount of ticks that are left for the car to get to that point
    def get_ticks_to_goal(self, collision_x, collision_y):
        point = pygame.Rect(collision_x, collision_y, 1, 1)
        ticks = -1
        passed = self.check_if_passed(point=point, point_x=collision_x, point_y=collision_y)
        if not passed:
            self.save_state()
            ticks = 0
            while not self.screen_car.colliderect(point):
                self.move_control()
                ticks += 1
            self.reverse()
        return ticks

    def calculate_new_acceleration(self, goal_ticks, collision_x, collision_y):
        pass
