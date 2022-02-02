# import cv2
import time
import imagezmq
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

    def __init__(self, image_processing_server_url: str = None) -> None:
        """
        Instantiates a MultiProcess Communications session and set up the necessary variables.
        Upon instantiation, RPi begins connecting to
        - Android   (o)
        - Algorithm (o)
        - STM       (x)
        in this exact order.
        Also instantiates the queues required for multiprocessing.
        """

        print("[Main] Initialising Multi Processing Communication")
        self.manager   = Manager()
        self.stm       = STM()
        self.android   = Android()
        self.algorithm = Algorithm()
        
        self.image_process = None
        self.image_processing_server = image_processing_server_url

        self.message_queue = self.manager.Queue()
        self.to_android_message_queue = self.manager.Queue()
        
        # Reading Process
        self.read_from_stm_process = Process(target=self.read_from_stm, name="[Read STM Process]")
        self.read_from_android_process = Process(target=self.read_from_android, name="[Read Android Process]")
        self.read_from_algorithm_process = Process(target=self.read_from_algorithm, name="[Read Algorithm Process]")

        # Writing Process
        self.write_to_target_process = Process(target=self.write_to_target, name="[Write to Target Process]")
        # self.write_to_android_process = Process(target=self.write_to_android, name="[Write Android Process]")

        # Image Processing
        if self.image_processing_server is not None:
            self.image_count = Value('i', 0)
            self.image_queue = self.manager.Queue()
            self.image_process = Process(target=self.image_processing, name="[Image Process]")

        self.process_list = [
            self.read_from_stm_process,
            self.read_from_android_process,
            self.read_from_algorithm_process,
            self.write_to_target_process,
            self.image_process,
            #self.write_to_android_process,
        ]

    # Start all processes -> Called from main.py
    def start(self) -> None:
        try:
            # STM Process
            self.stm.connect() 
            print("[Main] Established connection with STM.")

            # Android Process
            self.android.connect()
            print("[Main] Established connection with Android.")
            
            # Algorithm Process
            self.algorithm.connect()
            print("[Main] Established connection with Algorithm.")

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
        self.reconnection_check()

    # Shut down all processes -> Called from main.py
    def end(self) -> None:
        self.stm.disconnect()
        self.android.disconnect_all()
        self.algorithm.disconnect_all()
        print("[Main] Multi Process Communication has successfully ended.")


    def reconnection_check(self) -> None:
        while True:
            try:
                # Check STM connection
                if not self.read_from_stm_process.is_alive():
                    self.reconnect_stm()

                # Check -> Android connection
                if not self.read_from_android_process.is_alive():
                    self.reconnect_android()
                
                # Check -> Algorithm Connection.
                if not self.read_from_algorithm_process.is_alive():
                    self.reconnect_algorithm()
                
                if not self.write_to_target_process.is_alive():
                    pass

                if self.image_process is not None and not self.image_process.is_alive():
                   self.image_process.terminate()
                    
            except Exception as error:
                print("[Main] Error during reconnection: ",error)
                raise error

    """
    1. RPI
    Function: Write towards Target (Algorithm, STM).
    """
    def write_to_target(self):
        while True:
            target = None
            try:
                if not self.message_queue.empty(): #if not empty queue
                    message = self.message_queue.get_nowait()
                    target, payload = message['target'], message['payload']
                    if target == ALGORITHM_HEADER:
                        print(f"[Main] Writing to Algorithm: {payload}")
                        self.algorithm.write(payload)

                    elif target == STM_HEADER:
                        print(f"[Main] Writing to STM: {payload}")
                        self.stm.write(payload)

                    else:
                        print("[Main] Invalid Writing Target")

            except Exception as error:
                print("[Main] Error Writing to Target")
                self.error_message(error)

    """
    2.1 Android Read
    Function: Continuously read from Android using android.read() routine.
    Potential Redirection: Algorithm, RPI
    """
    def read_from_android(self) -> None:
        while True:
            try:
                raw_message = self.android.read()
                
                if raw_message is None: 
                    continue

                for message in raw_message.splitlines():
                    if len(message) <=0:
                        continue
    
                    if message == AndroidToAlgorithm.DEMO_ANDROID_TO_ALGO_MSG:
                        self.message_queue.put_nowait(self.format_message(ALGORITHM_HEADER, message))
                    else:
                        self.message_queue.put_nowait(self.format_message(ALGORITHM_HEADER, message))

            except Exception as error:
                print("[Main] Process of reading android has failed")
                self.error_message(error)

    """
    2.2 Android Write
    Function: Constantly Check if there's anything to Write to Android by checking android_message_queue
    """
    def write_to_android(self) -> None:
        while True:
            try:
                if not self.to_android_message_queue.empty():
                    message = self.to_android_message_queue.get_nowait()
                    self.android.write(message)
                
            except Exception as error:
                print('[Main] Process write_to_android has failed')
                self.error_message(error)

    """
    2.3 Reconnect to android 
    Function: Disconnect Android Process as well as Read & Write  to/from Android Process
    """ 
    def reconnect_android(self) -> None:
        print("[Main] Disconnecting Android Process.")

        # Terminate all Android process.
        self.read_from_android_process.terminate()
        # self.write_to_android_process.terminate()

        # Close all Android bluetooth sockets.
        self.android.disconnect()

        # Reconnect android
        self.android.connect()

        # Recreate all processes as Process cant be restart
        self.read_from_android_process = Process(target=self.read_from_android, name="[Read Android Process]")
        self.read_from_android_process.start()
        # self.write_to_android_process = Process(target=self.write_to_android, name="[Write Android Process]")
        # self.write_to_android_process.start()

        print("[Main] Android Process has been Reconnected")

    """
    3.1 Algo Read
    Function: Continuously read from Algorithm using algorithm.read() routine.
    Potential Redirection: Android, RPI, STM
    """
    def read_from_algorithm(self) -> None:
        while True:
            try:
                raw_message = self.algorithm.read()

                if raw_message is None:
                    continue

                message_list = raw_message.split(MESSAGE_SEPARATOR)
            
                if len(message_list) <=0:
                    continue
                print(message_list)
                if message_list[0] == AlgorithmToAndroid.DEMO_ALGO_TO_ANDROID_MSG:
                    print("[Main] Send to Android from Algorithm")
                    self.to_android_message_queue.put_nowait(message_list[1])
                
                elif message_list[0] == AlgorithmToRPI.TAKE_PICTURE:

                    if self.image_count.value >= 5:
                        self.message_queue.put_nowait(self.format_message(ALGORITHM_HEADER, RPIToAlgorithm.IMAGE_REC_DONE)) #remove newline
                    
                    else:
                        image = self.take_picture()
                        print('[Main] - RPI Picture Taken')
                        self.image_queue.put_nowait([image, message_list[0]])
                        self.message_queue.put_nowait(self.format_message(ALGORITHM_HEADER, RPIToAlgorithm.TAKE_PICTURE_DONE)) #remove newline
                    
            except Exception as error:
                print("[Main] Error Reading Algorithm Process")
                self.error_message(error)

    """
    2.3 Reconnect to android 
    Function: Disconnect Android Process as well as Read & Write  to/from Android Process
    """ 
    def reconnect_algorithm(self) -> None:
        print("[Main] Disconnecting Algorithm Process.")

        # Terminate all Android process.
        self.read_from_algorithm_process.terminate()
        self.write_to_target_process.terminate()
    
        # Close all Android bluetooth sockets.
        self.algorithm.disconnect()

        # Reconnect android
        self.algorithm.connect()

        # Recreate all processes as Process cant be restart
        self.read_from_algorithm_process = Process(target=self.read_from_algorithm, name="[Read Algorithm Process]")
        self.write_to_target_process = Process(target=self.write_to_target, name="[Write to Target Process]")

        self.read_from_algorithm_process.start()
        self.write_to_target_process.start()
        
        print("[Main] Android Process has been Reconnected")

    """
    4.1 STM Read
    Function: Continuously read from STM using stm.read() routine.
    Potential Redirection: Algorithm
    """

    def read_from_stm(self) -> (None):
        
        while True:
            try:
                message = self.stm.read()
                if message is None:
                    continue
                self.message_queue.put_nowait(self.format_message(ALGORITHM_HEADER, message + NEWLINE))
            except Exception as error:
                print('[Main] STM Read Error')
                self.error_message(error)
                break

    def reconnect_stm(self) -> None:
        print("[Main] Disconnecting STM Process.")

        # Terminate all Android process.
        self.read_from_stm_process.terminate()
        self.write_to_target_process.terminate()
    
        # Close all Android bluetooth sockets.
        self.stm.disconnect()

        # Reconnect android
        self.stm.connect()

        # Recreate all processes as Process cant be restart
        self.read_from_stm_process = Process(target=self.read_from_stm, name="[Read STM Process]")
        self.write_to_target_process = Process(target=self.write_to_target, name="[Write to Target Process]")

        self.read_from_stm_process.start()
        self.write_to_target_process.start()
        
        print("[Main] Android Process has been Reconnected")

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
                    reply = image_sender.send_image(
                        "RPI Image:" + str(start_time.strftime("%d%m%H%M%S")), 
                        image_message[0]
                    )
                    
                    reply = reply.decode(FORMAT)

                    # all images has been sent & processed.
                    if reply == 'Done':
                        break  
                    
                    detected_images = reply.split(MESSAGE_SEPARATOR)
                    
                    for detected in detected_images:
                        if detected not in image_id_list:
                            self.image_count.value += 1
                            image_id_list.put_nowait(detected)
                        self.to_android_message_queue.put_nowait(AlgorithmToAndroid.DETECTED + NEWLINE)
                    print(f'[Main] Time taken to process image: {str(datetime.now() - start_time)} seconds')

            except Exception as error:
                print('[Main] Error - Image processing failed')
                self.error_message(error)

    def format_message(self, target, payload) -> dict:
        return {"target" : target, "payload": payload}
    
    def error_message(self, message : str) -> None:
        print(f"[Error Message]: {message}")