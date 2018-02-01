

# Behaviour will be create a Channel and then add cars to it, when added the channel will send NewCarMessage
class Channel(object):

    def __init__(self, car_list=None):
        self.cars = car_list  # It is a list of Car objects
        if car_list is None:
            self.cars = []

    def add_car(self, car):
        self.cars.append(car)

    def delete_car(self, name):
        self.cars.remove(name)

    def broadcast(self, message):
        # Adds car to list if it is a new car message and it is not already in the list

        for car in self.cars:
            car.receive_message(message)

        if message.is_left_intersection_message():
            self.delete_car(message.get_sender_name())

    def get_cars(self):
        return self.cars

    def set_cars(self, car_list):
        self.cars = car_list

    def clean_channel(self):
        self.cars = []
