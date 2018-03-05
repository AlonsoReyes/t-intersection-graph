import unittest
from models.car import *
from models.channel import Channel
from random import randint, choice
from utils.utils import do_round


class TestCoordination(unittest.TestCase):
    def setUp(self):
        self.intention_list = ['l', 's', 'r']
        self.ticks = 15
        self.channel = Channel()
        self.test_case = {1: {'lane': 0, 'intention': 's', 'tick': 0},
                          2: {'lane': 0, 'intention': 'l', 'tick': 1},
                          3: {'lane': 3, 'intention': 'l', 'tick': 3},
                          4: {'lane': 1, 'intention': 'r', 'tick': 5},
                          5: {'lane': 2, 'intention': 's', 'tick': 7}}

    # Car enters intersection, sends NewCarMessage, next tick it is the supervisor
    def test_coordination_ticks(self):
        channel = Channel()
        car = Car(name=1, lane=randint(0, 3), intention=choice(self.intention_list),
                  channel=channel, pos_x=randint(0, 3), pos_y=randint(0, 3))
        self.assertEqual(None, car.get_supervisor_car())
        do_round(cars=[car], channel=channel)
        car.enter_intersection()
        do_round(cars=[car], channel=channel)
        self.assertTrue(1 in car.get_graph())
        self.assertEqual([], list(car.get_following_cars().keys()))
        self.assertEqual(1, car.get_supervisor_car())
        self.assertEqual(None, car.get_second_at_charge())

    # Car enters intersection, next tick it needs to be the supervisor and in that tick another car enters
    # it becomes the second at charge in that tick or next, depending on the management of the messages
    def test_second_at_charge_message(self):
        channel = Channel()
        sup_car = Car(name=1, lane=randint(0, 3), intention=choice(self.intention_list),
                      channel=channel, pos_x=randint(0, 3), pos_y=randint(0, 3))
        second_car = Car(name=2, lane=randint(0, 3), intention=choice(self.intention_list),
                         channel=channel, pos_x=randint(0, 3), pos_y=randint(0, 3))
        do_round([sup_car], channel)
        sup_car.enter_intersection()
        self.assertEqual(None, sup_car.get_supervisor_car())
        do_round([sup_car, second_car], channel)
        second_car.enter_intersection()
        self.assertTrue(sup_car.is_supervisor())
        self.assertTrue(1 in sup_car.get_graph() and 2 in sup_car.get_graph())
        self.assertEqual(None, second_car.get_supervisor_car())
        do_round([sup_car, second_car], channel)
        self.assertEqual(1, second_car.get_supervisor_car())
        self.assertTrue(second_car.is_second_at_charge())

    def test_three_car_coordination(self):
        channel = Channel()
        sup_car = Car(name=1, lane=randint(0, 3), intention=choice(self.intention_list),
                      channel=channel, pos_x=randint(0, 3), pos_y=randint(0, 3))
        second_car = Car(name=2, lane=randint(0, 3), intention=choice(self.intention_list),
                         channel=channel, pos_x=randint(0, 3), pos_y=randint(0, 3))
        normal_car = Car(name=3, lane=randint(0, 3), intention=choice(self.intention_list),
                         channel=channel, pos_x=randint(0, 3), pos_y=randint(0, 3))
        do_round([sup_car], channel)
        sup_car.enter_intersection()
        do_round([sup_car, second_car], channel)
        second_car.enter_intersection()
        do_round([sup_car, second_car, normal_car], channel)
        normal_car.enter_intersection()
        do_round([sup_car, second_car, normal_car], channel)
        self.assertEqual(1, normal_car.get_supervisor_car())
        self.assertEqual(2, normal_car.get_second_at_charge())
        self.assertFalse(normal_car.is_supervisor() or normal_car.is_second_at_charge())

    # Uses the same scenario from last test but with fixed intentions and lanes to produce collision and
    # check if InfoMessages are being sent/received and that follow list is created correctly
    def test_info_messages(self):
        channel = Channel()
        sup_car = Car(name=1, lane=0, intention='s',
                      channel=channel, pos_x=1, pos_y=1)
        second_car = Car(name=2, lane=1, intention='s',
                         channel=channel, pos_x=2, pos_y=2)
        normal_car = Car(name=3, lane=3, intention='l',
                         channel=channel, pos_x=3, pos_y=3)
        # Car 1 enters
        do_round([sup_car], channel)
        sup_car.enter_intersection()
        self.assertTrue(1 in sup_car.get_leaf_cars())
        # Car 2 enters and Car 1 becomes supervisor, Car 1 sends info message before Car 2 enters
        do_round([sup_car, second_car], channel)
        second_car.enter_intersection()
        # Car 3 enters and Car2 receives WelcomeMessage and Second At Charge, Car 1 and Car 2 send Info
        # before Car 3 enters
        do_round([sup_car, second_car, normal_car], channel)
        # Check leaf cars update
        self.assertEqual({2}, sup_car.get_leaf_cars())
        self.assertEqual({2}, second_car.get_leaf_cars())
        # Check info message from sup_car and follow lists
        self.assertEqual({}, sup_car.get_following_cars())
        self.assertEqual([1], list(second_car.get_following_cars().keys()))
        self.assertEqual(1, second_car.get_following_cars()[1]['pos_x'])
        normal_car.enter_intersection()
        # Car 3 receives Welcome Message
        do_round([sup_car, second_car, normal_car], channel)
        self.assertEqual({3}, sup_car.get_leaf_cars())
        self.assertEqual({3}, second_car.get_leaf_cars())
        self.assertEqual({3}, normal_car.get_leaf_cars())
        self.assertEqual([1], list(second_car.get_following_cars().keys()))
        self.assertEqual([2], list(normal_car.get_following_cars().keys()))
        self.assertTrue(2, normal_car.get_following_cars()[2]['pos_x'])

    def test_leave_intersection_supervisor(self):
        channel = Channel()
        sup_car = Car(name=1, lane=0, intention='s',
                      channel=channel, pos_x=1, pos_y=1)
        second_car = Car(name=2, lane=1, intention='s',
                         channel=channel, pos_x=2, pos_y=2)
        normal_car = Car(name=3, lane=3, intention='l',
                         channel=channel, pos_x=3, pos_y=3)
        last_car = Car(name=4, lane=3, intention='l',
                       channel=channel, pos_x=4, pos_y=4)
        # Car 1 enters
        do_round([sup_car], channel)
        sup_car.enter_intersection()
        # Car 2 enters and Car 1 becomes supervisor
        do_round([sup_car, second_car], channel)
        second_car.enter_intersection()
        # Car 3 enters and Car2 receives WelcomeMessage and Second At Charge
        do_round([sup_car, second_car, normal_car], channel)
        normal_car.enter_intersection()
        # Car 3 receives Welcome Message
        do_round([sup_car, second_car, normal_car, last_car], channel)
        last_car.enter_intersection()
        # Last car receives Welcome here
        do_round([sup_car, second_car, normal_car, last_car], channel)
        # Extra round
        do_round([sup_car, second_car, normal_car, last_car], channel)
        sup_car.leave_inner_intersection()
        self.assertTrue(second_car.is_supervisor())
        self.assertEqual(2, second_car.get_supervisor_car())
        self.assertEqual(3, second_car.get_second_at_charge())
        self.assertEqual(2, normal_car.get_supervisor_car())
        self.assertEqual(None, normal_car.get_second_at_charge())
        self.assertEqual(2, last_car.get_supervisor_car())
        self.assertEqual(None, last_car.get_second_at_charge())
        # Car3 receives SecondAtChargeMessage from Car 2
        do_round([sup_car, second_car, normal_car, last_car], channel)
        self.assertTrue(normal_car.is_second_at_charge())
        self.assertEqual(3, last_car.get_second_at_charge())

    def test_second_at_charge_leave(self):
        channel = Channel()
        car1 = Car(name=1, lane=0, intention='l', channel=channel)
        do_round([car1], channel)
        car1.enter_intersection()
        for i in range(4):
            do_round([car1], channel)
        self.assertTrue(car1.is_supervisor())
        car2 = Car(name=2, lane=1, intention='l', channel=channel)
        do_round([car1, car2], channel)
        car2.enter_intersection()
        car3 = Car(name=3, lane=2, intention='s', channel=channel)
        do_round([car1, car2, car3], channel)
        car3.enter_intersection()
        car4 = Car(name=4, lane=2, intention='r', channel=channel)
        do_round([car1, car2, car3, car4], channel)
        car4.enter_intersection()
        # follow lists:
        # 1: []
        # 2: [1]
        # 3: [2]
        # 4: [3]
        channel.do_round()
        for car in [car1, car2, car3, car4]:
            self.assertEqual([1, 2], [car.get_supervisor_car(), car.get_second_at_charge()])
        # Before car 2 leaves
        self.assertEqual([], list(car1.get_following_cars().keys()))
        self.assertEqual([1], list(car2.get_following_cars().keys()))
        self.assertEqual([2], list(car3.get_following_cars().keys()))
        self.assertEqual([3], list(car4.get_following_cars().keys()))
        for car in [car1, car2, car3, car4]:
            self.assertEqual({4}, car.get_leaf_cars())
        do_round([car1, car2, car3, car4], channel)
        car2.leave_inner_intersection()
        do_round([car1, car2, car3, car4], channel)
        for car in [car1, car3, car4]:
            self.assertEqual([1, 3], [car.get_supervisor_car(), car.get_second_at_charge()])
        self.assertEqual([1, None], [car2.get_supervisor_car(), car2.get_second_at_charge()])
        self.assertTrue(car1.is_supervisor())
        self.assertTrue(car3.is_second_at_charge())
        self.assertFalse(car4.is_supervisor())
        self.assertFalse(car4.is_second_at_charge())
        for car in [car1, car2, car3, car4]:
            self.assertTrue(2 not in car.get_graph())
            for node in car.get_graph().values():
                self.assertTrue(2 not in node.get_follow_list())
        # After
        self.assertEqual([], list(car1.get_following_cars().keys()))
        self.assertEqual([1], list(car2.get_following_cars().keys()))
        self.assertEqual([], list(car3.get_following_cars().keys()))
        self.assertEqual([3], list(car4.get_following_cars().keys()))
