
class PointInt:
    def __init__(self):
        self.x = 0
        self.y = 0


class Datamatrix:
    def __init__(self, code_string="", coordinates=None,
                 angle=float(0), cost_time=float(0), as_byte=b''):
        if coordinates is None:
            coordinates = [PointInt(0, 0), PointInt(0, 0), PointInt(0, 0), PointInt(0, 0)]
        self.code_string = code_string
        self.coordinates = coordinates  # 4x PointInt elements
        self.angle = angle
        self.cost_time = cost_time  # if we need to know time, elapse to encode this code
        self.as_byte = as_byte


