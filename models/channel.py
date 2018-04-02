import copy


# Behaviour will be create a Channel and then add cars to it, when added the channel will send NewCarMessage
class Channel(object):

    def __init__(self, messages_per_round=10, car_list=None, round_messages=None, next_round_messages=None):

        # Amount of messages that can be sent in a round. Works like a timeout. It's measured in quantity,
        # but the idea is the amount of messages that can be sent in a time interval.
        self.messages_per_round = messages_per_round
        # Counter of messages sent in the current round.
        self.messages_sent = 0
        self.cars = car_list  # It is a list of Car objects
        if car_list is None:
            self.cars = []

        # List of messages that are going to be sent in the current tick/round
        self.current_round_messages = round_messages
        if round_messages is None:
            self.current_round_messages = []

        # List where the messages are queued, they are gonna be sent in the next round.
        # They are the responses of the messages sent in the current round or InfoMessages
        self.next_round_messages = next_round_messages
        if next_round_messages is None:
            self.next_round_messages = []

        # Dictionaries that keep the last cars which left the inner intersection by lane of exit
        # and the same for entering the screen
        self.recent_leaving = {0: None, 1: None, 2: None, 3: None}
        self.recent_entering = {0: None, 1: None, 2: None, 3: None}

    def last_to_leave_notification(self, car):
        if car.get_sensor() is not None:
            car.get_sensor().set_closest_car(self.recent_leaving[car.destination_lane()])
        self.recent_leaving[car.destination_lane()] = car

    def last_to_enter_notification(self, car):
        if car.get_sensor() is not None:
            car.get_sensor().set_closest_car(self.recent_entering[car.get_lane()])
        self.recent_entering[car.get_lane()] = car

    def add_car(self, car):
        self.cars.append(car)

    def queue_message(self, message):
        self.next_round_messages.append(message)

    def deliver(self, message):
        for car in self.cars:
            car.receive_message(message)

    def broadcast(self, message):
        if message.is_info_message() or message.is_new_car_message() \
                or message.is_left_intersection_message():
            self.deliver(message)
            if message.is_left_intersection_message():
                self.delete_car(message.get_sender_name())
        else:
            self.queue_message(message)

    def prepare_round(self):
        self.current_round_messages = copy.deepcopy(self.next_round_messages)
        self.next_round_messages = []

    def update_cars(self):
        for car in self.cars:
            car.update()

    def delete_car(self, name):
        for i in range(len(self.cars)):
            if self.cars[i].get_name() == name:
                del self.cars[i]
                break

    def deliver_messages(self):
        for message in self.current_round_messages:
            self.deliver(message)

    def do_round(self):
        self.prepare_round()
        self.deliver_messages()
        # self.update_cars()

    def get_cars(self):
        return self.cars

    def set_cars(self, car_list):
        self.cars = car_list

    def clean_channel(self):
        self.cars = []

    def get_current_round_messages(self):
        return self.current_round_messages

    def get_next_round_messages(self):
        return self.next_round_messages

    def get_recent_leaving(self):
        return self.recent_leaving

    def get_recent_entering(self):
        return self.recent_entering
