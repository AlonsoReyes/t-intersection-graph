import unittest
from models.car import *
from models.sensor import ProximitySensor
from models.controller import accelerating_controller
from models.channel import Channel
from random import randint, choice
from utils.utils import do_round, random_car, create_sensor
import pygame


# full_intersection_rect = pygame.Rect(0, 0, 768, 768) 768 is the width and height, 0 0 is from that point
# intersection_rect = pygame.Rect(280, 280, 210, 210)
# Spawn positions
# outside_initial_positions = [(435, 868, 0, 0), (868, 345, 90, 1), (345, -98, 180, 2), (-98, 435, 270, 3)]
class TestMovement(unittest.TestCase):
    def setUp(self):
        self.full_intersection_rect = pygame.Rect(0, 0, 768, 768)
        self.inner_intersection_rect = pygame.Rect(280, 280, 210, 210)

    # Tests that the car won't crash against a stopped car in front of it
    def test_stop_before_crash(self):
        channel = Channel()
        # coordinates before the inner intersection for a car coming from lane 0
        before_intersection_x = 435
        before_intersection_y = self.inner_intersection_rect.top + self.inner_intersection_rect.height + 30
        # this car doesn't move
        first_car = random_car(name=1, pos_x=before_intersection_x,
                               pos_y=before_intersection_y, initial_speed=0, acceleration_rate=0,
                               full_intersection=self.full_intersection_rect, channel=channel,
                               inner_intersection=self.inner_intersection_rect, lane=0, intention='s',
                               create_sensor_flag=True, controller=accelerating_controller)
        do_round([first_car], channel)
        self.assertEqual(first_car, channel.get_recent_entering()[0])
        follower_car = random_car(name=2, initial_speed=40, full_intersection=self.full_intersection_rect,
                                  channel=channel, inner_intersection=self.inner_intersection_rect,
                                  lane=0, intention='s', create_sensor_flag=True, controller=accelerating_controller)
        do_round([first_car, follower_car], channel)
        for i in range(1000):
            do_round([first_car, follower_car], channel)
            self.assertFalse(follower_car.check_collision(first_car))

