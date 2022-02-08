# import cv2
import time
import imagezmq
import bluetooth
from misc.config import *
from misc.protocols import *
from picamera import PiCamera
from picamera.array import PiRGBArray

from datetime import datetime
from multiprocessing import Process, Value, Manager

from .stm import STM
from .android import Android
from .algorithm import Algorithm

class MultiProcessing:
    """
    Handles the communication between STM, Android, Algorithm and Image Processing Server.
    """    

    def __init__(self, image_processing_server: str = None) -> None:
        """
        - Android   (o)
        - Algorithm (o)
        - STM       (x)
        """

        print("[Main] Initialising Multi Processing Communication")
        self.manager   = Manager()
        #self.stm       = STM()
        self.android   = Android()
        self.algorithm = Algorithm()
        
        self.image_process = None

        # Message Queue - can't use pipe as theres multiple end points.
        self.to_stm_message_queue = self.manager.Queue()
        self.to_algo_message_queue = self.manager.Queue()
        self.to_android_message_queue = self.manager.Queue()
        
        # Reading Process
        #self.recv_from_stm_process = Process(target=self.recv_from_stm, name="[STM Recv Process]")
        self.recv_from_android_process = Process(target=self.recv_from_android, name="[Android Recv Process]")
        self.recv_from_algorithm_process = Process(target=self.recv_from_algorithm, name="[Algorithm Recv Process]")

        # Writing Process
        #self.send_to_stm_process = Process(target=self.send_to_stm, name = "[STM Send Process]")
        self.send_to_android_process = Process(target=self.send_to_android, name="[Android Send Process]")
        self.send_to_algorithm_process = Process(target=self.send_to_algorithm, name="[Algorithm Send Process]")

        # Image Processing
        if image_processing_server is not None:
            self.image_count = Value('i', 0)
            self.image_queue = self.manager.Queue()
            self.image_processing_server = image_processing_server
            self.image_process = Process(target=self.image_processing, name="[Image Process]")

        self.process_list = [
            #self.recv_from_stm_process,
            self.recv_from_android_process,
            self.recv_from_algorithm_process,
            #self.send_to_stm_process,
            self.send_to_android_process,
            self.send_to_algorithm_process,
            self.image_process,
        ]

    # Start all processes -> Called from main.py
    def start(self) -> None:
        try:
            # self.stm.connect() # STM Instance
            self.android.connect() # Android Instance
            self.algorithm.connect() # Algorithm Instance
            
            # Start all processes.
            for process in self.process_list:
                if process is None:
                    continue
                process.start()
                print(f"[Main] {process.name} has started.")

            print('[Main] Multi Process Communication has successfully started.')

        except Exception as error:
            self.format_message(error)
            raise error

        # Continously check if reconnection is needed.
        self.check_process_alive()

    # Shut down all processes -> Called from main.py
    def end(self) -> None:
        #self.stm.disconnect()
        self.android.disconnect_all()
        self.algorithm.disconnect_all()
        print("[Main] Multi Process Communication has successfully ended.")

    def check_process_alive(self) -> None:
        while True:
            try:
                # Check STM connection
                #if not self.recv_from_stm_process.is_alive() or not self.send_to_stm_process.is_alive():
                #   self.reconnect_stm()

                # Check -> Android connection
                if not self.recv_from_android_process.is_alive() or not self.send_to_android_process.is_alive():
                    self.reconnect_android()
                
                # Check -> Algorithm Connection.
                if not self.recv_from_algorithm_process.is_alive() or not self.send_to_algorithm_process.is_alive():
                    self.reconnect_algorithm()
                
                if self.image_process is not None and not self.image_process.is_alive():
                   self.image_process.terminate()
                    
            except Exception as error:
                print("[Main] Error during reconnection: ",error)
                raise error

    """
    1. Android Processes (Recv, Send) and function (reconnect_android)
    """

    """
    1.1 recv_from_android
    Function: Continuously read from Android using android.recv() routine.
    Potential Redirection: STM, Algorithm
    """
    def recv_from_android(self) -> None:
        while True:
            try:
                raw_message = self.android.recv()
                if raw_message is None: continue           

                for message in raw_message.split(MESSAGE_SEPARATOR):

                    if len(message) == 0: continue
                    
                    # Forward Android message to STM
                    if message in AndroidToSTM.MESSAGES:
                        # Mapping Android -> RPI <-> STM protocol.
                        self.to_stm_message_queue.put_nowait(self.format_message(ANDROID_HEADER, AndroidToSTM.MESSAGES[message]))
                    # Forward Android message to Algo
                    elif message.split(COMMAND_SEPARATOR)[0] in AndroidToAlgorithm.MESSAGES:
                        self.to_algo_message_queue.put_nowait(self.format_message(ANDROID_HEADER, message))
                    else:
                        print("[Main] No Forwarding : Message from Android: {message}")

            except Exception as error:
                print("[Main] Process of reading android has failed")
                # Peer has reset bluetooth network -> Restart now.
                self.reconnect_android()
                self.error_message(error)
    """
    1.2 send_to_android
    Function: Constantly Check if there's anything to Write to Android by checking android_message_queue
    """
    def send_to_android(self) -> None:
        while True:
            try:
                if not self.to_android_message_queue.empty():
                    message = self.to_android_message_queue.get_nowait()
                    self.android.send(message)
                
            except Exception as error:
                print('[Main] Process send_to_android has failed')
                self.error_message(error)

    """
    1.3 Reconnect to android 
    Function: Terminate android send/recv process and recreate them.
    """ 
    def reconnect_android(self) -> None:
        print("[Main] Disconnecting Android Process.")

        # Terminate all Android process.
        self.recv_from_android_process.terminate()
        self.send_to_android_process.terminate()
        print("[Main] Android send/recv processes has been terminated ")

        # Close all Android bluetooth sockets.
        self.android.disconnect_client()

        # Reconnect android
        self.android.connect()

        # Recreate all processes as Process cant be restart
        self.recv_from_android_process = Process(target=self.recv_from_android, name="[Android Recv Process]")
        self.send_to_android_process = Process(target=self.send_to_android, name="[Android Send Process]")
        self.recv_from_android_process.start()
        self.send_to_android_process.start()

        print("[Main] Android send/recv processes has been reconnected.")

    """
    2. Algorithm Processes (Recv, Send) and function (reconnect_algorithm)
    """

    """
    2.1 recv_from_algorithm
    Function: Continuously read from Algorithm using algorithm.recv() routine.
    Potential Redirection: Android, RPI, STM
    """
    def recv_from_algorithm(self) -> None:
        while True:
            try:
                raw_message = self.algorithm.recv()
                if raw_message is None: continue

                for message in raw_message.split(MESSAGE_SEPARATOR):

                    if message.split(COMMAND_SEPARATOR)[0] in AlgorithmToAndroid.MESSAGES:
                        self.to_android_message_queue.put_nowait(self.format_message(ALGORITHM_HEADER, message))
                    if message in AlgorithmToRPI.MESSAGES:
                        if message == AlgorithmToRPI.TAKE_PICTURE:
                            image = self.take_picture()
                            print('[Main] - RPI Picture Taken')
                            self.image_queue.put_nowait([image, message])
                            # self.message_queue.put_nowait(self.format_message(ALGORITHM_HEADER, RPIToAlgorithm.TAKE_PICTURE_DONE)) #remove newline                    
            except Exception as error:
                print("[Main] Error Reading Algorithm Process")
                self.error_message(error)

    """
    2.2 send_to_algorithm
    Function: Constantly Check if there's anything to send to algorithm by checking to_algo_message_queue
    """
    def send_to_algorithm(self) -> None:
        while True:
            try:
                if not self.to_algo_message_queue.empty():
                    message = self.to_algo_message_queue.get_nowait()
                    self.algorithm.send(message)
            except Exception as error:
                print('[Main] Process send_to_android has failed')
                self.error_message(error)

    """
    2.3 Reconnect to algorithm 
    Function: Terminate algorithm send/recv process and recreate them.
    """ 
    def reconnect_algorithm(self) -> None:

        print("[Main] Disconnecting Algorithm Process.")

        # Terminate all Android process.
        self.recv_from_algorithm_process.terminate()
        self.send_to_algorithm_process.terminate()
    
        # Close all Android bluetooth sockets.
        self.algorithm.disconnect()

        # Reconnect android
        self.algorithm.connect()

        # Recreate all processes as Process cant be restart
        self.recv_from_algorithm_process = Process(target=self.recv_from_algorithm, name="[Algorithm Recv Process]")
        self.send_to_algorithm_process = Process(target=self.send_to_algorithm, name="[Algorithm Send Process]")

        self.recv_from_algorithm_process.start()
        self.send_to_algorithm_process.start()
        
        print("[Main] Android Process has been Reconnected")

    """
    3. STM Processes (Recv, Send) and function (reconnect_stm)
    """

    """
    3.1 STM recv_from_stm
    Function: Continuously read from STM using stm.recv() routine.
    Potential Redirection: Algorithm
    """
    def recv_from_stm(self) -> (None):
        
        while True:
            try:
                #raw_message = self.stm.recv()
                raw_message = None
                if raw_message is None: continue

                for message in raw_message.split(MESSAGE_SEPARATOR):

                    if message is None:
                        continue

                    if message in STMToRPI.MESSAGES:
                        print(f"[Main] Recieve from STM: {message}")
                        
            except Exception as error:
                print('[Main] STM Read Error')
                self.error_message(error)
                break

    """
    3.2 send_to_stm
    Function: Constantly Check if there's anything to send to stm by checking to_stm_message_queue
    """
    def send_to_stm(self) -> None:
        while True:
            try:
                if not self.to_stm_message_queue.empty():
                    message = self.to_stm_message_queue.get_nowait()
                    #self.stm.send(message)
            except Exception as error:
                print('[Main] Process send_to_stm has failed')
                self.error_message(error)

    """
    3.3 Reconnect to stm 
    Function: Terminate stm send/recv process and recreate them.
    """ 

    def reconnect_stm(self) -> None:
        print("[Main] Disconnecting STM Process.")

        # Terminate all Android process.
        self.recv_from_stm_process.terminate()
        self.send_to_stm_process.terminate()
    
        # Close all Android bluetooth sockets.
        #self.stm.disconnect()

        # Reconnect android
        #self.stm.connect()

        # Recreate all processes as Process cant be restart
        self.recv_from_stm_process = Process(target=self.recv_from_stm, name="[STM Recv Process]")
        self.send_to_stm_process = Process(target=self.send_to_stm, name="[STM Send Process]")
        self.recv_from_stm_process.start()
        self.send_to_stm_process.start()
        print("[Main] STM Process has been Reconnected")

    """
    4. RPI Functions
    """
    def take_picture(self) -> None:
        try:
            start_time = datetime.now()

            # initialize the camera and grab a reference to the raw camera capture
            camera = PiCamera(resolution=(IMAGE_WIDTH, IMAGE_HEIGHT))  # '1920x1080'
            rawCapture = PiRGBArray(camera)
            
            # allow the camera to warmup
            time.sleep(0.1)
            
            # grab an image from the camera
            camera.capture(rawCapture, format=IMAGE_FORMAT)
            image = rawCapture.array
            camera.close()

            print('[Main] Time Take to take picture: ' + str(datetime.now() - start_time) + 'seconds')
            
            # to gather training images
            # os.system("raspistill -o images/test"+
            # str(start_time.strftime("%d%m%H%M%S"))+".png -w 1920 -h 1080 -q 100")
        
        except Exception as error:
            print("[Main] Failed to Take Picture.")
            self.error_message(error)
        
        return image

    def image_processing(self) -> None:
        # initialize the ImageSender object with the socket address of the server
        image_id_list = set()
        image_sender = imagezmq.ImageSender(connect_to=self.image_processing_server)
        while True:
            try:
                if not self.image_queue.empty():
                    start_time = datetime.now()
                    image_message =  self.image_queue.get_nowait()
                    print("[Main] Sending Image to Server.")
                    reply = image_sender.send_image("RPI Image:" + str(start_time.strftime("%d%m%H%M%S")), image_message[0])
                    
                    reply = reply.decode(FORMAT)

                    # all images has been sent & processed.
                    if reply == 'Done':
                        break  
                    
                    self.to_algo_message_queue.put_nowait(self.format_message(RPI_HEADER, "PICTURE/2/1".encode(FORMAT)))
                    self.to_android_message_queue.put_nowait(self.format_message(RPI_HEADER, "PICTURE/2/1".encode(FORMAT)))
                    print(f'[Main] Time taken to process image: {str(datetime.now() - start_time)} seconds')

                    """
                    detected_images = reply.split(MESSAGE_SEPARATOR)
                    
                    for detected in detected_images:
                        if detected not in image_id_list:
                            self.image_count.value += 1
                            image_id_list.put_nowait(detected)
                        self.to_android_message_queue.put_nowait(AlgorithmToAndroid.DETECTED + NEWLINE)
                    """
            except Exception as error:
                print('[Main] Error - Image processing failed')
                self.error_message(error)

    def format_message(self, header, message) -> dict:
        return header + message
    
    def error_message(self, message : str) -> None:
        print(f"[Error Message]: {message}")