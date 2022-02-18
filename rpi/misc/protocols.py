"""
Communication protocols.
For sub-systems communication purposes.
"""

NEWLINE = "\n".encode()
MESSAGE_SEPARATOR = "|".encode()
COMMAND_SEPARATOR = "/".encode() # ROBOT/x/y
COMMA_SEPARATOR = ",".encode()

RPI_HEADER = 'RPI|'.encode()
STM_HEADER = 'STM|'.encode()
ANDROID_HEADER = 'AND|'.encode()
ALGORITHM_HEADER = 'ALG|'.encode()

""" Source: STM """
# 6 Direction Command
COMMAND_W = "W".encode()
COMMAND_S = "S".encode()
COMMAND_A = "A".encode()
COMMAND_D = "D".encode()
COMMAND_Q = "Q".encode()
COMMAND_E = "E".encode()
# Flags 
ANGLE_0    = "x0000".encode()
ANGLE_30   = "x0030".encode()
DISTANCE   = "1500".encode()

class STM_MOVESET:
    # Command | D Flag | Distance | Direction | Angle Flag | Angle
    SETUP_ONE = "P0001x0001".encode()
    SETUP_TWO = "I0005x0005".encode()
    W = COMMAND_W + DISTANCE + ANGLE_0 # Moving Foward
    S = COMMAND_S + DISTANCE + ANGLE_0 # Moving Backward
    Q = COMMAND_Q + DISTANCE + ANGLE_30 # Moving Top Left
    E = COMMAND_E + DISTANCE + ANGLE_30 # Moving Top Right
    A = COMMAND_A + DISTANCE + ANGLE_30 # Moving Btm Left
    D = COMMAND_D + DISTANCE + ANGLE_30 # Moving Btm Right
    X = "X".encode()
    DONE = "M".encode()
    ANDROID_DONE = "DONE".encode() # Done for android
    ALGO_DONE = "ROBOT/NEXT".encode() # Done for algorithm
    
    # Map command to message
    MESSAGES = { W, S, Q, E, A, D, DONE, ANDROID_DONE, ALGO_DONE}

class STMToAndroid:
    STATUS = "STATUS".encode()
    DEBUG  = "DEBUG".encode()
    MESSAGES = {STATUS, DEBUG}

""" Source: Android """
class AndroidToSTM:
    MOVE_F  = "MOVE/F".encode()
    MOVE_R  = "MOVE/R".encode()
    MOVE_L  = "MOVE/L".encode()
    MOVE_B  = "MOVE/B".encode()
    MOVE_BL = "MOVE/BL".encode()
    MOVE_BR = "MOVE/BR".encode()
    STOP    = "STOP".encode()
    ANDTOSTM = "ANDTOSTM".encode() # Format : ALGTOAND/MESSAGE - For raw message
    MESSAGES = {
        MOVE_F : STM_MOVESET.W, 
        MOVE_R : STM_MOVESET.E,
        MOVE_L : STM_MOVESET.Q,
        MOVE_B : STM_MOVESET.S, 
        MOVE_BL: STM_MOVESET.A,
        MOVE_BR: STM_MOVESET.D,
        STOP   : STM_MOVESET.X,
        ANDTOSTM: ANDTOSTM
        }

class AndroidToAlgorithm:
    START  = "START".encode()
    STOP   = "STOP".encode()
    ANDTOALG = "ANDTOALG".encode() # Format : ANDTOALG/MESSAGE - For raw message
    MESSAGES = {START, STOP, ANDTOALG}

class AndroidToRPI:
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
    
""" Source: RPI """
class RPIToAlgorithm:
    PICTURE = "PICTURE".encode()
    IMAGE_REC_DONE = "Done Image Recogniton".encode()
    TAKE_PICTURE_DONE = "Done Taking Picture".encode()
    DEMO_RPI_TO_ALGO_MSG = "RPI_ALGO".encode()

class RPIToAndroid:
    FINISH_PATH = "FINISH/PATH".encode()
    FINISH_EXPLORE = "FINISH/EXPLORE".encode()
    DEMO_RPI_TO_AND_MSG = "RPI_AND".encode()

class RPIToSTM:
    DEMO_RPI_TO_STM_MSG = "RPI_STM".encode()
