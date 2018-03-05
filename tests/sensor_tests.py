import unittest
from models.car import *
from models.sensor import ProximitySensor
from models.sensor import ProximitySensor
from models.channel import Channel
from random import randint, choice
from utils.utils import do_round, random_car
import pygame


# full_intersection_rect = pygame.Rect(0, 0, 768, 768) 768 is the width and height, 0 0 is from that point
# intersection_rect = pygame.Rect(280, 280, 210, 210)
# Spawn positions
# outside_initial_positions = [(435, 868, 0, 0), (868, 345, 90, 1), (345, -100, 180, 2), (-100, 435, 270, 3)]
class TestSensor(unittest.TestCase):
    def setUp(self):
        self.full_intersection_rect = pygame.Rect(0, 0, 768, 768)
        self.inner_intersection_rect = pygame.Rect(280, 280, 210, 210)

    # Checks that it calculates correctly the number of ticks left to crash
    def test_ticks_to_crash_lane_0(self):
        channel = Channel()
        # coordinates before the inner intersection for a car coming from lane 0
        before_intersection_y = self.inner_intersection_rect.top + self.inner_intersection_rect.height + 30
        # this car doesn't move
        first_car = random_car(name=1,
                               pos_y=before_intersection_y, initial_speed=0, acceleration_rate=0,
                               full_intersection=self.full_intersection_rect, channel=channel,
                               inner_intersection=self.inner_intersection_rect, lane=0, intention='s')
        follower_car = random_car(name=2, initial_speed=40, full_intersection=self.full_intersection_rect,
                                  channel=channel, inner_intersection=self.inner_intersection_rect,
                                  lane=0, intention='s')
        sensor = ProximitySensor(owner_car=follower_car, closest_car=first_car)
        follower_car.set_sensor(sensor)
        self.assertEqual(35, sensor.ticks_to_crash())

    def test_ticks_to_crash_lane_1(self):
        channel = Channel()
        before_intersection_x = self.inner_intersection_rect.left + self.inner_intersection_rect.width + 30
        first_car = random_car(name=1, pos_x=before_intersection_x, initial_speed=0, acceleration_rate=0,
                               full_intersection=self.full_intersection_rect, channel=channel,
                               inner_intersection=self.inner_intersection_rect, lane=1, intention='s')
        follower_car = random_car(name=2, initial_speed=40, full_intersection=self.full_intersection_rect,
                                  channel=channel, inner_intersection=self.inner_intersection_rect,
                                  lane=1, intention='s')
        sensor = ProximitySensor(owner_car=follower_car, closest_car=first_car)
        follower_car.set_sensor(sensor)
        self.assertEqual(35, sensor.ticks_to_crash())

    def test_ticks_to_crash_lane_2(self):
        channel = Channel()
        before_intersection_x = 335
        before_intersection_y = self.inner_intersection_rect.top - 30
        first_car = random_car(name=1, pos_x=before_intersection_x,
                               pos_y=before_intersection_y, initial_speed=0, acceleration_rate=0,
                               full_intersection=self.full_intersection_rect, channel=channel,
                               inner_intersection=self.inner_intersection_rect, lane=2, intention='s')
        follower_car = random_car(name=2, initial_speed=40, full_intersection=self.full_intersection_rect,
                                  channel=channel, inner_intersection=self.inner_intersection_rect,
                                  lane=2, intention='s')
        sensor = ProximitySensor(owner_car=follower_car, closest_car=first_car)
        follower_car.set_sensor(sensor)
        print('test')
        self.assertEqual(35, sensor.ticks_to_crash())

    def test_ticks_to_crash_lane_3(self):
        channel = Channel()
        before_intersection_x = self.inner_intersection_rect.left - 30
        first_car = random_car(name=1, pos_x=before_intersection_x, initial_speed=0, acceleration_rate=0,
                               full_intersection=self.full_intersection_rect, channel=channel,
                               inner_intersection=self.inner_intersection_rect, lane=3, intention='s')
        follower_car = random_car(name=2, initial_speed=40, full_intersection=self.full_intersection_rect,
                                  channel=channel, inner_intersection=self.inner_intersection_rect,
                                  lane=3, intention='s')
        sensor = ProximitySensor(owner_car=follower_car, closest_car=first_car)
        follower_car.set_sensor(sensor)
        self.assertEqual(35, sensor.ticks_to_crash())

    def test_sensor_condition(self):
        channel = Channel()
        # coordinates before the inner intersection for a car coming from lane 0
        before_intersection_x = 435
        before_intersection_y = self.inner_intersection_rect.top + self.inner_intersection_rect.height + 30
        # this car doesn't move
        # LANE 0
        first_car = random_car(name=1, pos_x=before_intersection_x,
                               pos_y=before_intersection_y, initial_speed=0, acceleration_rate=0,
                               full_intersection=self.full_intersection_rect, channel=channel,
                               inner_intersection=self.inner_intersection_rect, lane=0, intention='s')
        follower_car = random_car(name=2, initial_speed=40, full_intersection=self.full_intersection_rect,
                                  channel=channel, inner_intersection=self.inner_intersection_rect,
                                  lane=0, intention='s')
        sensor = ProximitySensor(owner_car=follower_car, closest_car=first_car)
        follower_car.set_sensor(sensor)
        self.assertTrue(sensor.sensor_condition(follower_car.get_x_coordinate(), follower_car.get_y_coordinate(),
                                                follower_car.get_direction() * pi / 180,
                                                first_car.get_x_coordinate(), first_car.get_y_coordinate(),
                                                first_car.get_direction() * pi / 180))

        # LANE 1
        before_intersection_x = self.inner_intersection_rect.left + \
                                self.inner_intersection_rect.width + 30
        before_intersection_y = 345
        first_car = random_car(name=1, pos_x=before_intersection_x,
                               pos_y=before_intersection_y, initial_speed=0, acceleration_rate=0,
                               full_intersection=self.full_intersection_rect, channel=channel,
                               inner_intersection=self.inner_intersection_rect, lane=1, intention='s')
        follower_car = random_car(name=2, initial_speed=40, full_intersection=self.full_intersection_rect,
                                  channel=channel, inner_intersection=self.inner_intersection_rect,
                                  lane=1, intention='s')
        sensor = ProximitySensor(owner_car=follower_car, closest_car=first_car)
        follower_car.set_sensor(sensor)
        self.assertTrue(sensor.sensor_condition(follower_car.get_x_coordinate(), follower_car.get_y_coordinate(),
                                                follower_car.get_direction() * pi / 180,
                                                first_car.get_x_coordinate(), first_car.get_y_coordinate(),
                                                first_car.get_direction() * pi / 180))

        # LANE 2
        before_intersection_x = 435
        before_intersection_y = self.inner_intersection_rect.top - 30
        first_car = random_car(name=1, pos_x=before_intersection_x,
                               pos_y=before_intersection_y, initial_speed=0, acceleration_rate=0,
                               full_intersection=self.full_intersection_rect, channel=channel,
                               inner_intersection=self.inner_intersection_rect, lane=2, intention='s')
        follower_car = random_car(name=2, initial_speed=40, full_intersection=self.full_intersection_rect,
                                  channel=channel, inner_intersection=self.inner_intersection_rect,
                                  lane=2, intention='s')
        sensor = ProximitySensor(owner_car=follower_car, closest_car=first_car)
        follower_car.set_sensor(sensor)
        self.assertTrue(sensor.sensor_condition(follower_car.get_x_coordinate(), follower_car.get_y_coordinate(),
                                                follower_car.get_direction() * pi / 180,
                                                first_car.get_x_coordinate(), first_car.get_y_coordinate(),
                                                first_car.get_direction() * pi / 180))

        # LANE 3
        before_intersection_x = self.inner_intersection_rect.left - 30
        before_intersection_y = 345
        first_car = random_car(name=1, pos_x=before_intersection_x,
                               pos_y=before_intersection_y, initial_speed=0, acceleration_rate=0,
                               full_intersection=self.full_intersection_rect, channel=channel,
                               inner_intersection=self.inner_intersection_rect, lane=3, intention='s')
        follower_car = random_car(name=2, initial_speed=40, full_intersection=self.full_intersection_rect,
                                  channel=channel, inner_intersection=self.inner_intersection_rect,
                                  lane=3, intention='s')
        sensor = ProximitySensor(owner_car=follower_car, closest_car=first_car)
        follower_car.set_sensor(sensor)
        self.assertTrue(sensor.sensor_condition(follower_car.get_x_coordinate(), follower_car.get_y_coordinate(),
                                                follower_car.get_direction() * pi / 180,
                                                first_car.get_x_coordinate(), first_car.get_y_coordinate(),
                                                first_car.get_direction() * pi / 180))
