import unittest
from models.car import *
from models.channel import Channel
from random import randint, choice
from utils.utils import cars_cross_path


class TestCar(unittest.TestCase):

    def setUp(self):
        self.intention_list = ['l', 's', 'r']
        self.ticks = 10
        self.channel = Channel()

    def test_change_class(self):
        car = Car(name=0)
        self.assertEqual(True, car.test_method())

    def test_leave_intersection(self):
        pass

    def test_supervisor_leave(self):
        pass

    def test_second_at_charge_leave(self):
        pass

    def test_new_car_message(self):
        pass

    def test_add_cars_from_start(self):
        pass

    def test_add_car(self):
        channel_one = Channel()
        cars = [Car(name=i, channel=channel_one) for i in range(7)]
        nodes = [Node(name=1, lane=0, intention='s', follow_list=[]),
                 Node(name=2, lane=2, intention='s', follow_list=[]),
                 Node(name=3, lane=1, intention='r', follow_list=[1]),
                 Node(name=4, lane=2, intention='s', follow_list=[2]),
                 Node(name=5, lane=3, intention='l', follow_list=[2, 3]),
                 Node(name=6, lane=2, intention='l', follow_list=[4, 5])]
        graph = {}
        for node in nodes:
            graph[node.get_name()] = node
        for car in cars:
            car.set_leaf_cars({6})
        for car in cars:
            car.set_graph(graph)
        car = Car(name=7, lane=1, intention='s', channel=channel_one)
        follow_list = cars[0].get_graph()[car.get_name()].get_follow_list()
        self.assertEqual([6], follow_list)

    def test_supervisor_coordination(self):
        ticks_to_simulate = self.ticks
        car_list = []
        channel_two = Channel()

        for tick in range(ticks_to_simulate):
            # print(tick)
            if tick % 2 == 0:
                car_list.append(Car(name=int(tick / 2), lane=randint(0, 3), intention=choice(self.intention_list),
                                channel=channel_two))
            for car in car_list:
                car.update()
        for car in car_list:
            self.assertEqual([0, 1], [car.get_supervisor_car(), car.get_second_at_charge()])
        graph = car_list[0].get_graph()
        self.assertEqual([], graph[0].get_follow_list())
        #for node in graph:
        #    print(graph[node].get_name(), ":", graph[node].get_follow_list(), " ", graph[node].get_lane(),
        #          " ", graph[node].get_intention())

    def test_iterative_to_check_first(self):
        for i in range(1000):
            self.test_supervisor_coordination()


if __name__ == '__main__':
    unittest.main()
