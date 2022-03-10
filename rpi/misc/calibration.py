from .protocols import COMMAND_LIST

class Calibration:
    # Option 1 -> Initialise calibration, reference other protocol from multi-processing
    # Opton  2 -> Multiple calibration, import based on args, protocol also need reference
    # Option 3 -> 

    def __init__(self, env) -> None:
        
        self.MINUS_UNIT = 8
        self.FORWARD_DISTANCE  = 21
        self.BACKWARD_DISTANCE = 21
        
        self.FORWARD_ANGLE = "x0000"
        self.BACKWARD_ANGLE = "x0000"

        self.TURN_I = "I0900x0100".encode()
        self.TURN_P = "P1200x1100".encode()
        
        self.STRAIGHT_F_I = "I0900x0100".encode()
        self.STRAIGHT_F_P = "P1800x3300".encode()

        self.STRAIGHT_R_I = "I0900x0100".encode()
        self.STRAIGHT_R_P = "P1200x2300".encode()

        self.calibration_map = {}
        self.W = self.S = self.Q = self.E = self.A = self.D = None
        
        if env == "g-outdoor":
            # Not Done
            self.TURN_I = "I0900x0100".encode()
            self.TURN_P = "P1200x1100".encode()
            self.STRAIGHT_F_I = "I0900x0100".encode()
            self.STRAIGHT_F_P = "P1800x3300".encode()

            self.STRAIGHT_R_I = "I0900x0100".encode()
            self.STRAIGHT_R_P = "P1200x2300".encode()

            self.W = [self.STRAIGHT_F_I, self.STRAIGHT_F_P, "W0013x0000".encode()]
            self.S = [self.STRAIGHT_F_I, self.STRAIGHT_F_P, "S0013x0000".encode()]
            self.Q = [self.TURN_I, self.TURN_P, "Q0105x2585".encode(), "S0019x0000".encode()]
            self.E = [self.TURN_I, self.TURN_P, "E0107x2242".encode(), "S0023x0000".encode()]
            self.A = [self.TURN_I, self.TURN_P, "W0027x0000".encode(), "A0117x2295".encode()]
            self.D = [self.TURN_I, self.TURN_P, "W0023x0000".encode(), "D0117x2295".encode()]

        if env == "outdoor":
            # Not Done
            self.TURN_I = "I0900x0100".encode()
            self.TURN_P = "P1200x1100".encode()
            self.STRAIGHT_F_I = "I0900x0100".encode()
            self.STRAIGHT_F_P = "P1800x3300".encode()

            self.STRAIGHT_R_I = "I0900x0100".encode()
            self.STRAIGHT_R_P = "P1200x2300".encode()

            self.W = [self.STRAIGHT_F_I, self.STRAIGHT_F_P, "W0013x0000".encode()]
            self.S = [self.STRAIGHT_F_I, self.STRAIGHT_F_P, "D0013x0140".encode()]
            self.Q = [self.TURN_I, self.TURN_P, "Q0105x2585".encode(), "S0019x0000".encode()]
            self.E = [self.TURN_I, self.TURN_P, "E0107x2242".encode(), "S0023x0000".encode()]
            self.A = [self.TURN_I, self.TURN_P, "W0027x0000".encode(), "A0117x2295".encode()]
            self.D = [self.TURN_I, self.TURN_P, "W0023x0000".encode(), "D0117x2295".encode()]

        elif env == "lab":
            self.TURN_I = "I0900x0100".encode()
            self.TURN_P = "P1200x1100".encode()
            self.STRAIGHT_F_I = "I0900x0100".encode()
            self.STRAIGHT_F_P = "P1800x3300".encode()

            self.STRAIGHT_R_I = "I0900x0100".encode()
            self.STRAIGHT_R_P = "P1200x2300".encode()

            self.W = [self.STRAIGHT_F_I, self.STRAIGHT_F_P, "Q0014x0194".encode()]
            self.S = [self.STRAIGHT_R_I, self.STRAIGHT_R_P, "D0014x0194".encode()]
            self.Q = [self.TURN_I, self.TURN_P, "Q0140x2755".encode(), "S0022x0000".encode()]
            self.E = [self.TURN_I, self.TURN_P, "E0131x2182".encode(), "S0022x0000".encode()]
            self.A = [self.TURN_I, self.TURN_P, "W0022x0000".encode(), "A0143x2681".encode()]
            self.D = [self.TURN_I, self.TURN_P, "W0020x0000".encode(), "D0131x2265".encode()]
        
        else:
            self.W = [self.STRAIGHT_F_I, self.STRAIGHT_F_P, "Q0014x0194".encode()]
            self.S = [self.STRAIGHT_F_I, self.STRAIGHT_F_P, "D0014x0194".encode()]
            self.Q = [self.TURN_I, self.TURN_P, "Q0101x2605".encode(), "S0019x0000".encode()]
            self.E = [self.TURN_I, self.TURN_P, "E0104x2330".encode(), "S0022x0000".encode()]
            self.A = [self.TURN_I, self.TURN_P, "W0022x0000".encode(), "A0114x2585".encode()]
            self.D = [self.TURN_I, self.TURN_P, "W0020x0000".encode(), "D0109x2400".encode()]

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
            return [self.STRAIGHT_F_I, self.STRAIGHT_F_P, ("W" + str(int(unit * self.FORWARD_DISTANCE) - self.MINUS_UNIT).rjust(4, '0') + self.FORWARD_ANGLE).encode()]
        else:
            return [self.STRAIGHT_R_I, self.STRAIGHT_R_P, ("S" + str(int(unit * self.BACKWARD_DISTANCE) - self.MINUS_UNIT).rjust(4, '0') + self.BACKWARD_ANGLE).encode()]
        

    def bundle_movement_raw(self, direction, unit):
        if direction == 0:
            return ("W" + str(int(unit * self.FORWARD_DISTANCE) - self.MINUS_UNIT).rjust(4, '0') + self.FORWARD_ANGLE).encode()
        else:
            return ("S" + str(int(unit * self.BACKWARD_DISTANCE) - self.MINUS_UNIT).rjust(4, '0') + self.BACKWARD_ANGLE).encode()
        
        