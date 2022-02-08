"""
Communication protocols.
For sub-systems communication purposes.
"""

NEWLINE = "\n".encode()
MESSAGE_SEPARATOR = "|".encode()
COMMAND_SEPARATOR = "/".encode() # ROBOT/x/y

RPI_HEADER = 'RPI|'.encode()
STM_HEADER = 'STM|'.encode()
ANDROID_HEADER = 'AND|'.encode()
ALGORITHM_HEADER = 'ALG|'.encode()

""" Source: STM """
class STMToRPI:
    H = "H".encode() # Connection established
    W = "fwd".encode() # Moving Foward
    D = "rgt".encode() # Moving Right
    A = "lft".encode() # Moving Left
    S = "S".encode() # Reverse
    X = "X".encode() # Stop
    L = "L".encode() # Three point turn left
    R = "R".encode() # Three point turn right

    F_, M_, G_, P_, V_, R_, E_ = 6, 13, 7, 16, 22, 18, 5

    F_ = F_.to_bytes(1, 'little')
    M_ = M_.to_bytes(1, 'little')
    G_ = G_.to_bytes(1, 'little')
    P_ = P_.to_bytes(1, 'little')
    V_ = V_.to_bytes(1, 'little')
    R_ = R_.to_bytes(1, 'little')
    E_ = E_.to_bytes(1, 'little')
    
    MESSAGES = {H, W, D, A, S, X, L, R, F_, M_, G_, P_, V_, R_, E_}

""" Source: Android """
class AndroidToSTM:
    MOVE_N = "MOVE/N".encode()
    MOVE_S = "MOVE/S".encode()
    MOVE_E = "MOVE/E".encode()
    MOVE_W = "MOVE/W".encode()
    STOP   = "STOP".encode()
    ANDTOSTM = "ANDTOSTM".encode() # Format : ALGTOAND/MESSAGE - For raw message
    MESSAGES = {MOVE_N: STMToRPI.W, MOVE_S: STMToRPI.S, MOVE_E: STMToRPI.D, MOVE_W: STMToRPI.A, STOP: STMToRPI.X, ANDTOSTM: ANDTOSTM}

class AndroidToAlgorithm:
    START  = "START".encode()
    CREATE = "CREATE".encode()
    FACE   = "FACE".encode()
    DELETE = "DELETE".encode()
    ANDTOALG = "ANDTOALG".encode() # Format : ANDTOALG/MESSAGE - For raw message
    MESSAGES = {START, CREATE, FACE, DELETE, ANDTOALG}

class AndroidToRPI:
    DEMO_ANDROID_TO_RPI_MSG = "AND_RPI".encode()

""" Source: Algorithm """
class AlgorithmToAndroid:
    ROBOT  = "ROBOT".encode()
    STATUS = "STATUS".encode()
    ALGTOAND = "ALGTOAND".encode() # Format : ALGTOAND/MESSAGE - For raw message
    MESSAGES = {ROBOT, STATUS}

class AlgorithmToRPI:
    TAKE_PICTURE = "TAKE_PICTURE".encode()
    MESSAGES = {TAKE_PICTURE}

class AlgorithmToSTM:
    ALGTOSTM = "ALGTOSTM".encode() # Format : ALGTOAND/MESSAGE - For raw message
    MOVE_N = "MOVE/N".encode()
    MOVE_S = "MOVE/S".encode()
    MOVE_E = "MOVE/E".encode()
    MOVE_W = "MOVE/W".encode()
    STOP   = "STOP".encode()
    ANDTOSTM = "ANDTOSTM".encode() # Format : ALGTOAND/MESSAGE - For raw message
    MESSAGES = {ALGTOSTM : ALGTOSTM, MOVE_N: STMToRPI.W, MOVE_S: STMToRPI.S, MOVE_E: STMToRPI.D, MOVE_W: STMToRPI.A, STOP: STMToRPI.X}
    
""" Source: RPI """
class RPIToAlgorithm:
    PICTURE = "PICTURE".encode()
    IMAGE_REC_DONE = "Done Image Recogniton".encode()
    TAKE_PICTURE_DONE = "Done Taking Picture".encode()
    DEMO_RPI_TO_ALGO_MSG = "RPI_ALGO".encode()

class RPIToAndroid:
    DEMO_RPI_TO_AND_MSG = "RPI_AND".encode()

class RPIToSTM:
    DEMO_RPI_TO_STM_MSG = "RPI_STM".encode()
