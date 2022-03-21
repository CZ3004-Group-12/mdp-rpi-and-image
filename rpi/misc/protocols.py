NEWLINE = "\n".encode()
AND_HEADER = "&".encode()
COMMA_SEPARATOR = ",".encode()
SLASH_SEPARATOR = "/".encode() # ROBOT/x/y
MESSAGE_SEPARATOR = "|".encode()

RPI_HEADER = 'RPI|'.encode()
STM_HEADER = 'STM|'.encode()
ANDROID_HEADER = 'AND|'.encode()
DEBUG_HEADER = "DEBUG/".encode()
ALGORITHM_HEADER = 'ALG|'.encode()

""" Source: STM """
class COMMAND_LIST:
    F  = "F".encode()
    B  = "B".encode()
    FR = "FR".encode()
    FL = "FL".encode()
    BR = "BR".encode()
    BL = "BL".encode()

class STM_TASK2:
    IR = "S".encode()
    BRAKE = "B".encode() # Brake.
    FORWARD = "W9999x0000".encode()  # Move forward no stoage.
    TURN_LEFT = "Q0122x2620".encode() # Turn left
    TURN_RIGHT = "U".encode() # 180 turn
    DONE    = "0000000000".encode()
    
    MESSAGES = {IR, BRAKE, FORWARD, TURN_LEFT, TURN_RIGHT}

class STM_PROTOCOL:
    SETUP_I = "I0900x0100".encode()
    SETUP_P = "P1200x1100".encode()
    DONE    = "0000000000".encode()
    SETUP_DONE   = "00000000000000000000".encode()
    MESSAGES = { SETUP_I, SETUP_P, DONE, SETUP_DONE}

class STMToAndroid:
    STATUS = "STATUS".encode()
    DONE   = "DONE/".encode()
    DEBUG  = "DEBUG".encode()
    MESSAGES = {STATUS, DEBUG}

class AlgorithmToSTM:
    # MOVEMENTS/10-9/B,B,B,FL,F,F,F,F,F,FL,B,B,F,F,F,BR,F,F,FROBOT/10-9/(11.0, 2.0, -90)/(10.0, 2.0, -90)/(9.0, 2.0, -90)/(12.0, 5.0, 0)/(12.0, 6.0, 0)/(12.0, 7.0, 0)/(12.0, 8.0, 0)/(12.0, 9.0, 0)/(12.0, 10.0, 0)/(9.0, 13.0, 90)/(10.0, 13.0, 90)/(11.0, 13.0, 90)/(10.0, 13.0, 90)/(9.0, 13.0, 90)/(8.0, 13.0, 90)/(11.0, 16.0, 180)/(11.0, 15.0, 180)/(11.0, 14.0, 180)/(11.0, 13.0, 180)
    ALGTOSTM       = "ALGTOSTM".encode() # Format : ALGTOAND/MESSAGE - For raw message
    MOVEMENTS      = "MOVEMENTS".encode()
    MESSAGES  = { ALGTOSTM : ALGTOSTM, MOVEMENTS: MOVEMENTS}

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
        START : 1, 
        ANDTOSTM: 1,
        MOVE_F : [COMMAND_LIST.F], 
        MOVE_B : [COMMAND_LIST.B],
        MOVE_R : [COMMAND_LIST.FR], 
        MOVE_L : [COMMAND_LIST.FL],
        MOVE_BL: [COMMAND_LIST.BL],
        MOVE_BR: [COMMAND_LIST.BR],
        }

class AndroidToAlgorithm:
    EXPLORE = "EXPLORE".encode()
    ANDTOALG = "ANDTOALG".encode() # Format : ANDTOALG/MESSAGE - For raw message
    MESSAGES = {EXPLORE, ANDTOALG}

class AndroidToRPI:
    START  = "START".encode()
    STOP   = "STOP".encode()

""" Source: Algorithm """
class AlgorithmToAndroid:
    ROBOT  = "ROBOT".encode()
    DEBUG = "DEBUG".encode()
    MESSAGES = {ROBOT, DEBUG}

class AlgorithmToRPI:
    OBSTACLE = "OBSTACLE".encode()
    TAKE_PICTURE = "TAKE_PICTURE".encode()
    MESSAGES = {TAKE_PICTURE, OBSTACLE}

""" Source: RPI """
class RPIToAlgorithm:
    NIL = "NIL".encode()
    REQUEST_ROBOT_NEXT = "ROBOT/NEXT/".encode() # Done for algorithm

class RPIToAndroid:
    FINISH_PATH = "FINISH/PATH".encode()
    FINISH_EXPLORE = "FINISH/EXPLORE".encode()
