from .protocols import COMMAND_LIST

class Calibration:
    # Option 1 -> Initialise calibration, reference other protocol from multi-processing
    # Opton  2 -> Multiple calibration, import based on args, protocol also need reference
    # Option 3 -> 

    def __init__(self, env) -> None:
        
        self.MINUS_UNIT = 8
        self.FORWARD_DISTANCE  = 20.3
        self.BACKWARD_DISTANCE = 20.3

        self.FORWARD_ANGLE = "x0000"
        self.BACKWARD_ANGLE = "x0000"

        self.calibration_map = {}
        self.W = self.S = self.Q = self.E = self.A = self.D = None
        
        if env == "g-outdoor":
            self.W = ["W0013x0000".encode()]
            self.S = ["S0013x0000".encode()]
            self.Q = ["Q0105x2585".encode(), "S0019x0000".encode()]
            self.E = ["E0107x2242".encode(), "S0023x0000".encode()]
            self.A = ["W0027x0000".encode(), "A0117x2295".encode()]
            self.D = ["W0023x0000".encode(), "D0117x2295".encode()]

        if env == "outdoor":
            self.W = ["W0013x0000".encode()]
            #self.W = ["Q0013x0140".encode()]
            self.S = ["D0013x0140".encode()]
            self.Q = ["Q0105x2585".encode(), "S0019x0000".encode()]
            self.E = ["E0107x2242".encode(), "S0023x0000".encode()]
            self.A = ["W0027x0000".encode(), "A0117x2295".encode()]
            self.D = ["W0023x0000".encode(), "D0117x2295".encode()]

        elif env == "lab":
            self.W = ["Q0014x0194".encode()]
            self.S = ["D0014x0194".encode()]
            self.Q = ["Q0101x2605".encode(), "S0019x0000".encode()]
            self.E = ["E0104x2330".encode(), "S0022x0000".encode()]
            self.A = ["W0022x0000".encode(), "A0114x2585".encode()]
            self.D = ["W0020x0000".encode(), "D0109x2400".encode()]
        
        else:
            self.W = ["Q0014x0194".encode()]
            self.S = ["D0014x0194".encode()]
            self.Q = ["Q0101x2605".encode(), "S0019x0000".encode()]
            self.E = ["E0104x2330".encode(), "S0022x0000".encode()]
            self.A = ["W0022x0000".encode(), "A0114x2585".encode()]
            self.D = ["W0020x0000".encode(), "D0109x2400".encode()]

        self.calibration_map = {
            COMMAND_LIST.F: self.W,
            COMMAND_LIST.B: self.S,
            COMMAND_LIST.BL: self.A,
            COMMAND_LIST.BR: self.D,
            COMMAND_LIST.FR: self.E,
            COMMAND_LIST.FL: self.Q,
        }

    def bundle_movement(self, direction, unit) -> list:
        if direction == 0:
            return [("W" + str(int(unit * self.FORWARD_DISTANCE) - self.MINUS_UNIT).rjust(4, '0') + self.FORWARD_ANGLE).encode()]
        else:
            return [("S" + str(int(unit * self.BACKWARD_DISTANCE) - self.MINUS_UNIT).rjust(4, '0') + self.BACKWARD_ANGLE).encode()]
        

    def bundle_movement_raw(self, direction, unit):
        if direction == 0:
            return ("W" + str(int(unit * self.FORWARD_DISTANCE) - self.MINUS_UNIT).rjust(4, '0') + self.FORWARD_ANGLE).encode()
        else:
            return ("S" + str(int(unit * self.BACKWARD_DISTANCE) - self.MINUS_UNIT).rjust(4, '0') + self.BACKWARD_ANGLE).encode()
        
        