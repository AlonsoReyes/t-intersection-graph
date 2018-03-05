import pygame
from models.channel import Channel
from models.sensor import ProximitySensor
from models.controller import accelerating_controller
from utils.utils import random_car, do_round, init_graphic_environment

full_intersection_rect = pygame.Rect(0, 0, 768, 768)
inner_intersection_rect = pygame.Rect(280, 280, 210, 210)


def simulate_stop_before_crash(first_car_speed=10.0, follower_car_speed=40.0, first_lane=0, follower_lane=0,
                               first_intention='s', follower_intention='s', iterations=1000):
    screen_width = 768
    screen, background, intersection_background, font = init_graphic_environment(screen_width, 768)
    channel = Channel()
    # coordinates before the inner intersection for a car coming from lane 0
    if first_lane == 0:
        before_intersection_x = 435
        before_intersection_y = inner_intersection_rect.top + inner_intersection_rect.height + 50
    elif first_lane == 1:
        before_intersection_x = inner_intersection_rect.left + inner_intersection_rect.width + 50
        before_intersection_y = 335
    elif first_lane == 2:
        before_intersection_x = 335
        before_intersection_y = inner_intersection_rect.top - 50
    else:
        before_intersection_x = inner_intersection_rect.left - 50
        before_intersection_y = 435
    # this car doesn't move
    first_car = random_car(pos_x=before_intersection_x, pos_y=before_intersection_y,
                           name=1, initial_speed=first_car_speed, acceleration_rate=0,
                           full_intersection=full_intersection_rect, channel=channel,
                           inner_intersection=inner_intersection_rect, lane=first_lane, intention=first_intention,
                           create_sensor_flag=True)
    follower_car = random_car(name=2, initial_speed=follower_car_speed, full_intersection=full_intersection_rect,
                              channel=channel, inner_intersection=inner_intersection_rect,
                              lane=follower_lane, intention=follower_intention,
                              create_sensor_flag=True)
    for i in range(iterations):
        screen.blit(background, (0, 0))
        screen.blit(intersection_background, (0, 0))
        for car in [first_car, follower_car]:
            screen.blit(car.rotated_image, car.screen_car)
        """
        if first_car.inside_inner_intersection():
            print('first')
            print(first_car.get_position())
        if follower_car.inside_inner_intersection():
            print('second')
            print(follower_car.get_position())
        #print(first_car.get_direction())
        """
        # print(follower_car.get_acceleration())
        pygame.display.update(screen.get_rect())
        do_round([first_car, follower_car], channel)
    pygame.display.quit()


if __name__ == '__main__':
    simulate_stop_before_crash(first_car_speed=0.0, follower_car_speed=20.0, first_lane=3, follower_lane=3,
                               first_intention='s', follower_intention='s', iterations=200)


