from .protocols import COMMAND_LIST

class Calibration:
    # Option 1 -> Initialise calibration, reference other protocol from multi-processing
    # Opton  2 -> Multiple calibration, import based on args, protocol also need reference
    # Option 3 -> 

    def __init__(self, env) -> None:
        
        # Task 2
        self.MINUS_UNIT = 8
        self.FORWARD_DISTANCE  = 21
        self.BACKWARD_DISTANCE = 21
        
        self.TURN_I = "I0900x0100".encode()
        self.TURN_P = "P1200x1100".encode()
        
        self.STRAIGHT_F_I = "I0900x0100".encode()
        self.STRAIGHT_F_P = "P1800x3300".encode()

        self.STRAIGHT_R_I = "I0900x0100".encode()
        self.STRAIGHT_R_P = "P1200x2300".encode()

        self.calibration_map = {}
        self.MAX_FORWARD = None
        self.W = self.S = self.Q = self.E = self.A = self.D = None
        
        if env == "lab":
            self.TURN_I = "I0900x0100".encode()
            self.TURN_P = "P1200x1100".encode()
            self.STRAIGHT_F_I = "I0900x0100".encode()
            self.STRAIGHT_F_P = "P1200x2100".encode()

        elif env == "outdoor":
            # Not Done
            self.TURN_I = "I0900x0100".encode()
            self.TURN_P = "P1200x1100".encode()
            self.STRAIGHT_F_I = "I0900x0100".encode()
            self.STRAIGHT_F_P = "P1200x3500".encode()

        else:
            self.TURN_I = "I0900x0100".encode()
            self.TURN_P = "P1200x1100".encode()
            self.STRAIGHT_F_I = "I0900x0100".encode()
            self.STRAIGHT_F_P = "P1800x3300".encode()

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
        
        