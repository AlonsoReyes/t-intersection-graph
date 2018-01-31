

# The list of cars that a car follows is a dictionary where the keys are the names
# and the value is another dictionary with the information of the car that I need to know
def prepare_follow_list(car_list):
    car_dict = {}
    default_dictionary = {'pos_x': None, 'pos_y': None, 'speed': None, 'acceleration': None}
    for name in car_list:
        car_dict[name] = dict(default_dictionary)
    return car_dict


# Used in add_new_car method
def delete_from_list(node, node_list):
    for i in range(len(node_list)):
        if node_list[i].get_name() == node.get_name():
            del node_list[i]
            break


def cars_cross_path(car_lane, car_intention, other_car_lane, other_car_intention):
    """
    Check if the path of one car crosses tih the path o f another. It is true if the other car is the same lane
    or if the other car is in one of the perpendicular lanes.
    :param car_lane: lane of the car
    :param car_intention: intention of a car
    :param other_car_intention: the intention of way of the other car
    :param other_car_lane: the lane at which the other car star its way.
    :return: True if the paths does not crosses, False otherwise.
    """
    lane_to_int_dict = {"l": 0, "s": 1, "r": 2}
    table0 = [[True, True, True], [True, True, True], [True, True, True]]
    table1 = [[True, True, False], [True, True, False], [False, True, False]]
    table2 = [[True, True, True], [True, False, False], [True, False, False]]
    table3 = [[True, True, False], [True, True, True], [False, False, False]]
    all_tables = [table0, table1, table2, table3]
    return all_tables[(car_lane - other_car_lane) % 4][lane_to_int_dict[car_intention]][
        lane_to_int_dict[other_car_intention]]
