"""
Communication protocols.
For sub-systems communication purposes.
"""

NEWLINE = "\n".encode()
MESSAGE_SEPARATOR = "|".encode()
COMMAND_SEPARATOR = "/".encode() # ROBOT/x/y
COMMA_SEPARATOR = ",".encode()
AND_HEADER = "&".encode()

DEBUG_HEADER = "DEBUG/".encode()
RPI_HEADER = 'RPI|'.encode()
STM_HEADER = 'STM|'.encode()
ANDROID_HEADER = 'AND|'.encode()
ALGORITHM_HEADER = 'ALG|'.encode()

""" Source: STM """
#F,F,F,F,F,F,F,F,F,F,F,F,F,F,F,F,F
# 6 Direction Command
FORWARD_DISTANCE  = 20.3
FORWARD_ANGLE = "x0194"
BACKWARD_DISTANCE = 20.3
BACKWARD_ANGLE = "x0194"

"""
    Lab Movement calibration.
    W       = ["Q0014x0194".encode()]
    S       = ["D0014x0194".encode()]
    Q       = ["Q0101x2605".encode(), "S0019x0000".encode()]
    E       = ["E0104x2330".encode(), "S0022x0000".encode()]
    A       = ["W0022x0000".encode(), "A0114x2585".encode()]
    D       = ["W0020x0000".encode(), "D0109x2400".encode()]
"""
class STM_MOVESET:
    # Command | D Flag | Distance | Direction | Angle Flag | Angle
    SETUP_I = "I0900x0100".encode()
    SETUP_P = "P1200x1100".encode()
    W       = ["Q0013x0140".encode()]
    S       = ["D0013x0140".encode()]
    Q       = ["Q0105x2585".encode(), "S0019x0000".encode()]
    E       = ["E0107x2242".encode(), "S0023x0000".encode()]
    A       = ["W0027x0000".encode(), "A0117x2295".encode()]
    D       = ["W0023x0000".encode(), "D0117x2295".encode()]
    DONE    = "0000000000".encode()
    SETUP_DONE   = "00000000000000000000".encode()
    
    # Map command to message
    MESSAGES = { SETUP_I, SETUP_P, DONE, SETUP_DONE}

class STMToAndroid:
    STATUS = "STATUS".encode()
    DONE   = "DONE/".encode()
    DEBUG  = "DEBUG".encode()
    MESSAGES = {STATUS, DEBUG}

class AlgorithmToSTM:
    ALGTOSTM       = "ALGTOSTM".encode() # Format : ALGTOAND/MESSAGE - For raw message
    MOVEMENTS      = "MOVEMENTS".encode()
    FORWARD        = "F".encode()
    BACKWARD       = "B".encode()
    FORWARD_RIGHT  = "FR".encode()
    FORWARD_LEFT   = "FL".encode()
    BACKWARD_RIGHT = "BR".encode()
    BACKWARD_LEFT  = "BL".encode()

    MESSAGES  = {
        ALGTOSTM : ALGTOSTM,
        MOVEMENTS: MOVEMENTS,
        FORWARD: STM_MOVESET.W,
        BACKWARD: STM_MOVESET.S,
        FORWARD_LEFT: STM_MOVESET.Q,
        FORWARD_RIGHT: STM_MOVESET.E,
        BACKWARD_LEFT: STM_MOVESET.A,
        BACKWARD_RIGHT: STM_MOVESET.D,
        }

""" Source: Android """
class AndroidToSTM:
    START = "START".encode()
    MOVE_F  = "MOVE/F".encode()
    MOVE_R  = "MOVE/R".encode()
    MOVE_L  = "MOVE/L".encode()
    MOVE_B  = "MOVE/B".encode()
    MOVE_BL = "MOVE/BL".encode()
    MOVE_BR = "MOVE/BR".encode()
    ANDTOSTM = "ANDTOSTM".encode() # Format : ALGTOAND/MESSAGE - For raw message
    MESSAGES = {
        START : START,
        MOVE_F : [AlgorithmToSTM.FORWARD], 
        MOVE_R : [AlgorithmToSTM.FORWARD_RIGHT], 
        MOVE_L : [AlgorithmToSTM.FORWARD_LEFT], 
        MOVE_B : [AlgorithmToSTM.BACKWARD], 
        MOVE_BL: [AlgorithmToSTM.BACKWARD_LEFT], 
        MOVE_BR: [AlgorithmToSTM.BACKWARD_RIGHT], 
        ANDTOSTM: ANDTOSTM,
        }

class AndroidToAlgorithm:
    EXPLORE = "EXPLORE".encode()
    ANDTOALG = "ANDTOALG".encode() # Format : ANDTOALG/MESSAGE - For raw message
    MESSAGES = {EXPLORE, ANDTOALG}

class AndroidToRPI:
    START  = "START".encode()
    STOP   = "STOP".encode()
    DEMO_ANDROID_TO_RPI_MSG = "AND_RPI".encode()

""" Source: Algorithm """
class AlgorithmToAndroid:
    ROBOT  = "ROBOT".encode()
    DEBUG = "DEBUG".encode()
    ALGTOAND = "ALGTOAND".encode() # Format : ALGTOAND/MESSAGE - For raw message
    MESSAGES = {ROBOT, DEBUG, ALGTOAND}

class AlgorithmToRPI:
    OBSTACLE = "OBSTACLE".encode()
    TAKE_PICTURE = "TAKE_PICTURE".encode()
    MESSAGES = {TAKE_PICTURE, OBSTACLE}

""" Source: RPI """
class RPIToAlgorithm:
    REQUEST_ROBOT_NEXT    = "ROBOT/NEXT".encode() # Done for algorithm

class RPIToAndroid:
    FINISH_PATH = "FINISH/PATH".encode()
    FINISH_EXPLORE = "FINISH/EXPLORE".encode()
    DEMO_RPI_TO_AND_MSG = "RPI_AND".encode()
