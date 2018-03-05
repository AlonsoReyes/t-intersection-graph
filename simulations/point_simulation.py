from models.channel import Channel
from models.car import *
from utils.utils import random_car, do_round, init_graphic_environment

full_intersection_rect = pygame.Rect(0, 0, 768, 768)
inner_intersection_rect = pygame.Rect(280, 280, 210, 210)


def simulate_stop_before_crash(first_car_speed=10.0, first_lane=0,
                               first_intention='s', iterations=1000,
                               collision_x=335, collision_y=345):
    screen_width = 768
    screen, background, intersection_background, font = init_graphic_environment(screen_width, 768)
    channel = Channel()
    first_car = random_car(name=1, initial_speed=first_car_speed, acceleration_rate=5,
                           full_intersection=full_intersection_rect, channel=channel,
                           inner_intersection=inner_intersection_rect, lane=first_lane, intention=first_intention,
                           create_sensor_flag=True)
    simulation_car = SimulationCar(first_car)
    ticks = simulation_car.get_ticks_to_goal(collision_x, collision_y)
    print(ticks)
    for i in range(iterations):
        screen.blit(background, (0, 0))
        screen.blit(intersection_background, (0, 0))
        screen.blit(simulation_car.rotated_image, simulation_car.screen_car)
        pygame.display.update(screen.get_rect())
        simulation_car.update()
        if simulation_car.collision_with_point(collision_x, collision_y):
            print('Collision with point: ' + str(i))
        if i > 140:
            print(simulation_car.get_ticks_to_goal(collision_x, collision_y))
            print(simulation_car.collision_with_point(collision_x, collision_y))
    pygame.display.quit()


if __name__ == '__main__':
    simulate_stop_before_crash(first_car_speed=10.0, first_lane=0,
                               first_intention='l', iterations=1000, collision_x=335, collision_y=345)


