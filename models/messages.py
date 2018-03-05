

class Message(object):

    def __init__(self, sender_car):
        self.sender_name = sender_car.get_name()

    def __eq__(self, other):
        if isinstance(other, type(self)) and self.sender_name == other.get_sender_name():
            if self.__class__ == other.__class__:
                return True
        return False

    # Some setters and getters
    def get_sender_name(self):
        return self.sender_name

    def set_sender_name(self, name):
        self.sender_name = name

    def is_new_car_message(self):
        return False

    def is_left_intersection_message(self):
        return False

    def is_welcome_message(self):
        return False

    def is_info_message(self):
        return False

    def is_second_at_charge_message(self):
        return False


class InfoMessage(Message):

    def __init__(self, sender_car):
        super(InfoMessage, self).__init__(sender_car)
        self.sender_position = sender_car.get_position()
        self.sender_lane = sender_car.get_lane()
        self.sender_direction = sender_car.get_direction()
        self.sender_speed = sender_car.get_speed()
        self.sender_acceleration = sender_car.get_acceleration()
        self.sender_intention = sender_car.get_intention()

    def is_info_message(self):
        return True

    def get_sender_position(self):
        return self.sender_position

    def set_sender_position(self, position):
        self.sender_position = position

    def get_sender_lane(self):
        return self.sender_lane

    def set_sender_lane(self, lane):
        self.sender_lane = lane

    def get_sender_direction(self):
        return self.sender_direction

    def set_sender_direction(self, direction):
        self.sender_direction = direction

    def get_sender_speed(self):
        return self.sender_speed

    def set_sender_speed(self, speed):
        self.sender_speed = speed

    def get_sender_acceleration(self):
        return self.sender_acceleration

    def set_sender_acceleration(self, acceleration):
        self.sender_acceleration = acceleration

    def get_sender_intention(self):
        return self.sender_intention

    def set_sender_intention(self, intention):
        self.sender_intention = intention


class NewCarMessage(Message):
    
    def __init__(self, sender_car):
        super(NewCarMessage, self).__init__(sender_car)
        self.sender_position = sender_car.get_position()
        self.sender_lane = sender_car.get_lane()
        self.sender_intention = sender_car.get_intention()
        self.sender_speed = sender_car.get_speed()
        self.sender_acceleration = sender_car.get_acceleration()

    def is_new_car_message(self):
        return True

    def get_sender_position(self):
        return self.sender_position

    def set_sender_position(self, position):
        self.sender_position = position

    def get_sender_lane(self):
        return self.sender_lane

    def set_sender_lane(self, lane):
        self.sender_lane = lane

    def get_sender_intention(self):
        return self.sender_intention

    def set_sender_intention(self, intention):
        self.sender_intention = intention

    def get_sender_speed(self):
        return self.sender_speed

    def set_sender_speed(self, speed):
        self.sender_speed = speed

    def get_sender_acceleration(self):
        return self.sender_acceleration

    def set_sender_acceleration(self, acceleration):
        self.sender_acceleration = acceleration


# Going to leave the checking of special cases to the car. Special cases like
# when the supervisor leaves the intersection or the second at charge.
class LeftIntersectionMessage(Message):

    def is_left_intersection_message(self):
        return True


# The supervisor sends this message to new cars. It is assumed that the supervisor
# modifies the graph before it sends this message
class WelcomeMessage(Message):

    def __init__(self, sender_car, receiver_name=None):
        super(WelcomeMessage, self).__init__(sender_car)
        self.receiver_name = receiver_name
        self.graph = sender_car.get_graph()
        self.leaf_cars = sender_car.get_leaf_cars()
        self.supervisor_name = sender_car.get_supervisor_car()
        self.second_at_charge_name = sender_car.get_second_at_charge()
        self.follow_list = {}

    def is_welcome_message(self):
        return True

    def get_receiver_name(self):
        return self.receiver_name

    def get_graph(self):
        return self.graph

    def set_graph(self, graph):
        self.graph = graph

    def get_supervisor(self):
        return self.supervisor_name

    def get_second_at_charge(self):
        return self.second_at_charge_name

    def get_follow_list(self, car_name):
        from utils.utils import prepare_follow_list
        return prepare_follow_list(self.get_graph()[car_name].get_follow_list())

    def get_leaf_cars(self):
        return self.leaf_cars

    def set_leaf_cars(self, car_set):
        self.leaf_cars = car_set


# It is used to tell a car that it is the second at charge
class SecondAtChargeMessage(Message):

    def __init__(self, sender_car, receiver_name=None):
        super(SecondAtChargeMessage, self).__init__(sender_car)
        self.receiver_name = receiver_name

    def is_second_at_charge_message(self):
        return True

    def get_receiver_name(self):
        return self.receiver_name
