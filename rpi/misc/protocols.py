"""
Communication protocols.
For sub-systems communication purposes.
"""

MESSAGE_SEPARATOR = ",".encode()
NEWLINE = "\n".encode()

STM_HEADER = 'STM'.encode()
ANDROID_HEADER = 'AND'.encode()
ALGORITHM_HEADER = 'ALG'.encode()

class AlgorithmToRPI:
    TAKE_PICTURE = "Take Picture".encode()
    DEMO_ALGO_TO_RPI_MSG = "ALGO_RPI".encode()

class AlgorithmToAndroid:
    DETECTED = "D".encode()
    DEMO_ALGO_TO_ANDROID_MSG = "ALGO_AND".encode()

class AlgorithmToSTM:
    DEMO_ALGO_TO_STMUINO_MSG = "ALGO_ADR".encode()

class AndroidToRPI:
    DEMO_ANDROID_TO_RPI_MSG = "AND_RPI".encode()

class AndroidToAlgorithm:
    DEMO_ANDROID_TO_ALGO_MSG = "AND_ALGO".encode()

class AndroidToSTM:
    DEMO_ANDROID_TO_STM_MSG = "AND_STM".encode()

class RPIToAlgorithm:
    IMAGE_REC_DONE = "Done Image Recogniton".encode()
    TAKE_PICTURE_DONE = "Done Taking Picture".encode()
    DEMO_RPI_TO_ALGO_MSG = "RPI_ALGO".encode()

class RPIToAndroid:
    DEMO_RPI_TO_AND_MSG = "RPI_AND".encode()

class RPIToSTM:
    DEMO_RPI_TO_STM_MSG = "RPI_STM".encode()
