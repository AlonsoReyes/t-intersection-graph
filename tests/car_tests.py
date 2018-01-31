import unittest
from models.car import *
from models.channel import Channel


class TestCar(unittest.TestCase):

    def setUp(self):
        self.channel = Channel()
        self.cars = [Car(name=i, channel=self.channel) for i in range(7)]
        nodes = [Node(name=1, lane=0, intention='s', follow_list=[]),
                 Node(name=2, lane=2, intention='s', follow_list=[]),
                 Node(name=3, lane=1, intention='r', follow_list=[1]),
                 Node(name=4, lane=2, intention='s', follow_list=[2]),
                 Node(name=5, lane=3, intention='l', follow_list=[2, 3]),
                 Node(name=6, lane=2, intention='l', follow_list=[4, 5])]
        graph = {}
        for node in nodes:
            graph[node.get_name()] = node
        for car in self.cars:
            car.set_leaf_cars({6})
        for car in self.cars:
            car.set_graph(graph)

    def test_add_car(self):
        car = Car(name=7, lane=1, intention='s', channel=self.channel)
        follow_list = self.cars[0].get_graph()[car.get_name()].get_follow_list()
        self.assertEqual([6], follow_list)


if __name__ == '__main__':
    unittest.main()