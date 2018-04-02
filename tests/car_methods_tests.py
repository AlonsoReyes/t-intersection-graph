import unittest
from models.car import *
from models.channel import Channel
from random import randint, choice
from utils.utils import do_round, random_car, graph_to_string
import pygame


# full_intersection_rect = pygame.Rect(0, 0, 768, 768) 768 is the width and height, 0 0 is from that point
# intersection_rect = pygame.Rect(280, 280, 210, 210)
# Spawn positions
# outside_initial_positions = [(435, 868, 0, 0), (868, 345, 90, 1), (345, -98, 180, 2), (-98, 435, 270, 3)]
class TestCarMethods(unittest.TestCase):
    def setUp(self):
        self.full_intersection_rect = pygame.Rect(0, 0, 768, 768)
        self.inner_intersection_rect = pygame.Rect(280, 280, 210, 210)
        self.default_channel = Channel()
        self.default_car = random_car(name=1, initial_speed=20, full_intersection=self.full_intersection_rect,
                                      channel=self.default_channel, inner_intersection=self.inner_intersection_rect,
                                      lane=0, intention='s')

    def test_enter_leave_method(self):
        self.default_car.enter_intersection()
        cars = self.default_channel.get_cars()
        self.assertEqual(self.default_car, cars[0])
        self.default_car.leave_inner_intersection()
        cars = self.default_channel.get_cars()
        self.assertEqual([], cars)

    def test_destination_lane(self):
        channel = Channel()
        car1 = random_car(name=1, initial_speed=20, full_intersection=self.full_intersection_rect, channel=channel,
                          inner_intersection=self.inner_intersection_rect, lane=0, intention='s')
        car2 = random_car(name=1, initial_speed=20, full_intersection=self.full_intersection_rect, channel=channel,
                          inner_intersection=self.inner_intersection_rect, lane=0, intention='l')
        car3 = random_car(name=1, initial_speed=20, full_intersection=self.full_intersection_rect, channel=channel,
                          inner_intersection=self.inner_intersection_rect, lane=0, intention='r')
        self.assertEqual(2, car1.destination_lane())
        self.assertEqual(3, car2.destination_lane())
        self.assertEqual(1, car3.destination_lane())

    # Tests that the car is added to the channel when it enters the screen and that the check methods are correct
    def test_enter_intersection(self):
        channel = Channel()
        car = random_car(name=1, initial_speed=20, full_intersection=self.full_intersection_rect, channel=channel,
                         inner_intersection=self.inner_intersection_rect, lane=0, intention='s')
        self.assertFalse(car.get_inside_full_rectangle())
        self.assertFalse(car.inside_full_intersection())
        self.assertTrue(car not in channel.get_cars())
        for _ in range(25):
            do_round([car], channel)
        self.assertTrue(car in channel.get_cars())
        self.assertTrue(car.get_inside_full_rectangle())
        self.assertTrue(car.inside_full_intersection())

    # Tests that the car exits the channel when it passes the inner intersection and that the check methods are correct
    def test_inner_intersection(self):
        channel = Channel()
        car = random_car(name=1, initial_speed=20, full_intersection=self.full_intersection_rect, channel=channel,
                         inner_intersection=self.inner_intersection_rect, lane=0, intention='s')
        self.assertFalse(car.inside_inner_intersection())
        for _ in range(91):
            do_round([car], channel)
        self.assertTrue(car.inside_inner_intersection())
        self.assertFalse(car.check_left_inner_intersection())
        for _ in range(66):
            do_round([car], channel)
        self.assertTrue(car not in channel.get_cars())
        self.assertTrue(car.check_left_inner_intersection())
        self.assertFalse(car.inside_inner_intersection())
        self.assertTrue(car.inside_full_intersection())
        # Checks that it continues working after being removed from the channel
        for _ in range(90):
            do_round([car], channel)

    # tests that add_new_car changes the graphs correctly
    def test_add_car(self):
        channel = Channel()
        cars = []
        lanes = [0, 2, 1, 2, 3, 2]
        intentions = ['s', 's', 'r', 's', 'l', 'l']
        for i in range(6):
            car = Car(name=(i + 1), lane=lanes[i], intention=intentions[i], channel=channel)
            cars.append(car)
            do_round(cars, channel)
            car.enter_intersection()

        do_round(cars, channel)
        # This should be the resulting graph after adding the 6 cars and the leaf cars should only contain the last car
        # number 6
        nodes = [Node(name=1, lane=0, intention='s', follow_list=[]),
                 Node(name=2, lane=2, intention='s', follow_list=[]),
                 Node(name=3, lane=1, intention='r', follow_list=[1]),
                 Node(name=4, lane=2, intention='s', follow_list=[2]),
                 Node(name=5, lane=3, intention='l', follow_list=[3, 4]),
                 Node(name=6, lane=2, intention='l', follow_list=[5])]
        graph = {}
        for node in nodes:
            graph[node.get_name()] = node
        for car in cars:
            # graph_to_string(car)
            self.assertEqual(graph, car.get_graph())
            self.assertEqual({6}, car.get_leaf_cars())
        car = Car(name=7, lane=1, intention='s', channel=channel)
        new_node = Node(name=7, lane=1, intention='s', follow_list=[6])
        graph[new_node.get_name()] = new_node
        # Note: the new leaf cars should be just number 7
        cars.append(car)
        do_round(cars, channel)
        car.enter_intersection()
        do_round(cars, channel)
        # asserting that the graphs are the same checks that the nodes contain the same information
        for car in cars:
            self.assertEqual(graph, car.get_graph())
            self.assertEqual({7}, car.get_leaf_cars())


