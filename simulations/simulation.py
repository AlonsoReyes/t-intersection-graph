from models.channel import Channel
from models.car import *
from models.messages import *
from models.node import Node
from random import randint

intention_list = ['l', 's', 'r']


def simulate_ticks(ticks=10):
    ticks_to_simulate = ticks
    cars = []
    channel = Channel()
    for tick in range(ticks_to_simulate):
        #print(tick)
        if tick % 2 == 0:
            cars.append(Car(name=tick, lane=randint(0, 3), intention=random.choice(intention_list),
                            channel=channel))
        for car in cars:
            car.update()

    for car in cars:
        print(str(car.get_supervisor_car()) + " " + str(car.get_second_at_charge()))


if __name__ == '__main__':
    simulate_ticks()
