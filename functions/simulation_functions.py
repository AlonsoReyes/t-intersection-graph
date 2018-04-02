import math
import random
import json
import time
from models.controller import algorithm_controller, accelerating_controller


# if I want a car to spawn every 3 ticks i should give 1/3 as an argument
def next_time(rate_parameter):
    return -math.log(1.0 - random.random()) / rate_parameter


def create_simulation_file(ticks=100, spawn_rate=1):
    from models.channel import Channel
    from utils.utils import random_car
    import os
    file = os.path.dirname(os.path.abspath(__file__)) + "/../simulation_files/" + str(ticks) + '_ticks'
    channel = Channel()
    cars = {'cars': []}
    lanes = [0, 1, 2, 3]
    intentions = ['l', 's', 'r']
    for name in range(ticks):
        if next_time(spawn_rate) <= spawn_rate:
            lane = random.choice(lanes)
            intention = random.choice(intentions)
            car = random_car(name=name, channel=channel, creation_time=name, lane=lane, intention=intention)
            cars['cars'].append(car.to_json())
    with open(file, 'w') as outfile:
        json.dump(cars, outfile)


def read_simulation_file(ticks, directory='/../simulation_files/'):
    import os
    root = os.path.dirname((os.path.abspath(__file__)))
    file = root + directory + str(ticks) + '_ticks'
    with open(file, 'r') as json_file:
        cars = json.load(json_file)
        return cars


def recreate_car(json_dict, channel, algorithm_flag=False):
    from models.car import Car
    from utils.utils import full_intersection_rect, inner_intersection_rect
    name = int(json_dict['name'])
    intention = json_dict['intention']
    lane = int(json_dict['lane'])
    creation_time = int(json_dict['creation_time'])
    initial_coordinates = json_dict['initial_coordinates']
    direction = float(initial_coordinates['direction'])
    pos_x = float(initial_coordinates['x_coordinate'])
    pos_y = float(initial_coordinates['y_coordinate'])
    return Car(name=name, pos_x=pos_x, pos_y=pos_y, lane=lane, intention=intention, direction=direction,
               channel=channel, algorithm_flag=algorithm_flag, sensor_flag=True, creation_time=creation_time,
               full_intersection=full_intersection_rect, inner_intersection=inner_intersection_rect,
               controller=accelerating_controller)


def collides_at_spawn(rect, other_car):
    collides = False
    if other_car is not None:
        if other_car.get_rect().colliderect(rect):
            collides = True
    return collides


def run_simulation(ticks, algorithm_flag=True, graphic_display=True, info_display=False, limit=150, car_limit=15):
    from utils.utils import init_graphic_environment, do_round
    from models.channel import Channel
    import pygame
    channel = Channel()
    cars = read_simulation_file(ticks)
    created_cars = {}
    car_queue = []
    if graphic_display:
        screen, background, intersection_background, font = init_graphic_environment()

    for tick in range(ticks):
        if tick == limit:
            break
        # print(tick)
        if car_limit >= len(list(created_cars.keys())):
            for index in range(len(cars['cars'])):
                if car_queue:
                    new_queue = []
                    for ind in range(len(car_queue)):
                        car = car_queue[ind]
                        lane = int(car['lane'])
                        length = 1
                        if channel.get_recent_entering()[lane] is not None:
                            length = channel.get_recent_entering()[lane].get_car_length()
                        coordinates = car['initial_coordinates']
                        rect = pygame.Rect(float(coordinates['x_coordinate']), float(coordinates['y_coordinate']), length,
                                           length)
                        rect.center = (float(coordinates['x_coordinate']), float(coordinates['y_coordinate']))
                        collides = collides_at_spawn(rect, channel.get_recent_entering()[lane])
                        if collides:
                            new_queue.append(car)
                        else:
                            created_cars[int(car['name'])] = recreate_car(car, channel, algorithm_flag=algorithm_flag)
                    car_queue = new_queue
                lane = int(cars['cars'][index]['lane'])
                length = 1
                if channel.get_recent_entering()[lane] is not None:
                    length = channel.get_recent_entering()[lane].get_car_length()
                car = cars['cars'][index]
                if int(car['creation_time']) <= tick:
                    coordinates = car['initial_coordinates']
                    rect = pygame.Rect(float(coordinates['x_coordinate']), float(coordinates['y_coordinate']), length, length)
                    rect.center = (float(coordinates['x_coordinate']), float(coordinates['y_coordinate']))
                    collides = collides_at_spawn(rect, channel.get_recent_entering()[lane])
                    #print(channel.get_recent_entering()[lane].get_acceleration())
                    #print(created_cars)
                    if collides:
                        car_queue.append(car)
                    else:
                        created_cars[int(car['name'])] = recreate_car(car, channel, algorithm_flag=algorithm_flag)
                else:
                    cars['cars'] = cars['cars'][index:]
                    break
        if graphic_display:
            screen.blit(background, (0, 0))
            screen.blit(intersection_background, (0, 0))
            for car in created_cars.values():
                screen.blit(car.rotated_image, car.screen_car)
            pygame.display.update(screen.get_rect())

        do_round(list(created_cars.values()), channel)

        if info_display:
            for car in created_cars.values():
                print('name: ' + str(car.get_name()) + ' controller: ' + car.get_controller().__name__ + ' left: '
                      + ' left_inner: ' + str(car.left_inner_rectangle) + ' tick: ' + str(tick)
                      + ' is_supervisor: ' + str(car.is_supervisor()) + ' is_second: ' + str(car.is_second_at_charge()) +
                      ' inside_full: ' + str(car.inside_full_rectangle))

    pygame.display.quit()


if __name__ == '__main__':
    #create_simulation_file(1000)
    run_simulation(1000, graphic_display=True, info_display=False, limit=400)

