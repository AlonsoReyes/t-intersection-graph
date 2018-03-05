
class Node(object):

    def __init__(self, name, follow_list, intention, lane):
        self.name = name
        self.follow_list = follow_list
        self.intention = intention
        self.lane = lane

    def __eq__(self, other):
        if isinstance(other, Node):
            if self.name == other.get_name() and self.follow_list == other.get_follow_list() \
                    and self.intention == other.get_intention() and self.lane == other.get_lane():
                return True
        return False

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def get_follow_list(self):
        return self.follow_list

    def set_follow_list(self, follow_list):
        self.follow_list = follow_list

    def get_intention(self):
        return self.intention

    def set_intention(self, intention):
        self.intention = intention

    def get_lane(self):
        return self.lane

    def set_lane(self, lane):
        self.lane = lane
