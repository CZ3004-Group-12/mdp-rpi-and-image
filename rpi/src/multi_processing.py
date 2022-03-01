import cv2
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
from .ultrasonic import UltraSonic

class MultiProcessing:
    """
    Handles the communication between STM, Android, Algorithm and Image Processing Server.
    """    
    
    def __init__(self, image_processing_server: str = None, android_on: bool = False, stm_on: bool = False, algo_on: bool = False, ultrasonic_on: bool = False, img_count: int = 5) -> None:
    
        """
        - Android   (o)
        - Algorithm (o)
        - STM       (o)
        """

        print("[Main] Initialising Multi Processing Communication")
        self.manager   = Manager()
        self.process_list = set()
        self.mode  = Value('i', 0) # 0: Manual, 1: Explore, 2: Path
        self.stm_ready_to_recv  = Value('i', 1)
        self.image_count = Value('i', img_count)
        self.stm = self.android = self.algorithm = self.image_process = self.ultrasonic = None

        # STM
        if stm_on:
            print("[Main] Running with STM") 
            self.stm = STM()
            self.to_stm_message_queue = self.manager.Queue()
            self.recv_from_stm_process = Process(target=self.recv_from_stm, name="[STM Recv Process]")
            self.send_to_stm_process = Process(target=self.send_to_stm, name = "[STM Send Process]")
            self.process_list.add(self.recv_from_stm_process)
            self.process_list.add(self.send_to_stm_process)
        
        # Android
        if android_on:
            print("[Main] Running with Android")  
            self.android = Android()
            self.to_android_message_queue = self.manager.Queue()
            self.recv_from_android_process = Process(target=self.recv_from_android, name="[Android Recv Process]")
            self.send_to_android_process = Process(target=self.send_to_android, name="[Android Send Process]")
            self.process_list.add(self.recv_from_android_process)
            self.process_list.add(self.send_to_android_process)

        # Algorithm
        if algo_on: 
            print("[Main] Running with Algorithm") 
            self.algorithm = Algorithm()
            self.to_algo_message_queue = self.manager.Queue()
            self.recv_from_algorithm_process = Process(target=self.recv_from_algorithm, name="[Algorithm Recv Process]")
            self.send_to_algorithm_process = Process(target=self.send_to_algorithm, name="[Algorithm Send Process]")
            self.process_list.add(self.recv_from_algorithm_process)
            self.process_list.add(self.send_to_algorithm_process)

        # Image Processing
        if image_processing_server is not None:
            print("[Main] Running with Image Processing")
            self.image_queue = self.manager.Queue()
            self.image_processing_server = image_processing_server
            self.image_process = Process(target=self.image_processing, name="[Image Process]")
            self.process_list.add(self.image_process)

        if ultrasonic_on:
            print("[Main] Running ultrasonic")
            self.ultrasonic = UltraSonic()
            self.recv_from_ultrasonic_process = Process(target=self.recv_from_ultrasonic, name="[Ultra Sonic Recv Process]")
            self.process_list.add(self.recv_from_ultrasonic_process)

    # Start all processes -> Called from main.py
    def start(self) -> None:
        try:
            # STM Instance
            if self.stm is not None:
                self.stm.connect()
            
            # Android Instance
            if self.android is not None:
                self.android.connect() 

            # Algorithm Instance
            if self.algorithm is not None:
                self.algorithm.connect() 
            
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
        if self.stm is not None: self.stm.disconnect()
        if self.android is not None: self.android.disconnect_all()
        if self.algorithm is not None: self.algorithm.disconnect_all()
        print("[Main] Multi Process Communication has successfully ended.")

    def check_process_alive(self) -> None:
        while True:
            try:
                # Check STM connection
                if self.stm is not None and (not self.recv_from_stm_process.is_alive() or not self.send_to_stm_process.is_alive()):
                   self.reconnect_stm()

                # Check -> Android connection
                if self.android is not None and (not self.recv_from_android_process.is_alive() or not self.send_to_android_process.is_alive()):
                    self.reconnect_android()
                
                # Check -> Algorithm Connection.
                if self.algorithm is not None and (not self.recv_from_algorithm_process.is_alive() or not self.send_to_algorithm_process.is_alive()):
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

                if raw_message is None: 
                    continue
                
                for message in raw_message.split(MESSAGE_SEPARATOR):
                    if len(message) == 0: 
                        continue
                    
                    if message in AndroidToSTM.MESSAGES:
                        # Mapping Android -> RPI <-> STM protocol.
                        if self.stm is None:
                            print("[Main] No Forwarding, as STM is not set-up.")
                            continue
                        # Set to manual mode
                        self.mode.value = 0
                        self.to_stm_message_queue.put_nowait(AndroidToSTM.MESSAGES[message])
                        continue

                    elif message == AndroidToRPI.STOP:
                        if self.stm is not None:
                            # Flush instructions & Reconnect
                            while not self.to_stm_message_queue.empty():
                                self.to_stm_message_queue.get_nowait()
                            print("[Main] - STM Message Queue has been flushed.")
                            self.reconnect_stm()
                        continue
                        
                    # Forward Android message to Algo
                    message_list = message.split(COMMAND_SEPARATOR)
                    if len(message_list) > 1 and message_list[0] == AndroidToRPI.START and message_list[1] == AndroidToAlgorithm.EXPLORE:
                        if self.algorithm is None:
                            print("[Main] No Forwarding, as Algo is not set-up.")
                            continue
                        # Set to explore mode
                        self.mode.value = 1
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
                    
                    # Split by '/'
                    commands = message.split(COMMAND_SEPARATOR)

                    if commands[0] in AlgorithmToSTM.MESSAGES:
                        
                        if self.stm is None:
                            print("[Main] No forwarding, as STM is not set-up.")
                            continue

                        # MOVEMENTS/4-15/B,B,B,B,FL,B,B,BR,F,F,F,F,F,F
                        if commands[0] == AlgorithmToSTM.MOVEMENTS:
                            print(f"[Main] - Current Target Obstacle: {commands[1]}")
                            movesets = commands[2].split(COMMA_SEPARATOR)
                            self.to_stm_message_queue.put_nowait(movesets)
                        else:    
                            print("[Main] Algorithm To STM Command Type not recognised.")
                        
                    elif commands[0] in AlgorithmToAndroid.MESSAGES:
                        if self.android is None:
                            print("[Main] No forwarding, as Android is not set-up.")
                            continue 
                        self.to_android_message_queue.put_nowait(self.format_message(AND_HEADER + ALGORITHM_HEADER, message))
    
                    elif commands[0] == AlgorithmToRPI.OBSTACLE:
                            image = self.take_picture()
                            print('[Main] - RPI Picture Taken')
                            self.image_queue.put_nowait([image, commands[1]])
                    else:
                        print("[Main] No forwarding, command not recognised.")

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
                raw_message = self.stm.recv()
                
                if raw_message is None:
                    continue

                for message in raw_message.split(MESSAGE_SEPARATOR):
                    if message is None or message is STM_MOVESET.SETUP_DONE:
                        continue
                    elif message not in STM_MOVESET.MESSAGES:
                        print("[Main] Command is not recognised under STM protocol. Please try again.")
                    elif message == STM_MOVESET.DONE:
                        time.sleep(.1)
                        self.stm_ready_to_recv.value = 1
                        print(f"[Main] Receive from STM: {message}")
                    else:
                        print(f"[Main] Doesn't match anything: received from STM: {message}")

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
                # Send only if STM is ready to receive.
                if self.to_stm_message_queue.empty() or self.stm_ready_to_recv.value != 1:
                    continue
                
                message = self.to_stm_message_queue.get_nowait()

                if isinstance(message, list):
                    commands = []
                    commands_len = []
                    index, length = 0, len(message)
                    # Truncating movement from [B, B, B, BR] -> [[Sxxxxxx], [Dxxx, Sxxx]]
                    while index < length:
                        curIndex = index
                        if message[index] == AlgorithmToSTM.FORWARD:
                            while curIndex < length and message[curIndex] == AlgorithmToSTM.FORWARD:
                                curIndex += 1
                            commands_len.append(curIndex - index)
                            commands.append([("Q" + str(int(((curIndex - index) * FORWARD_DISTANCE)-8)).rjust(4, '0') + FORWARD_ANGLE).encode()])
                            index = curIndex
                        elif message[index] == AlgorithmToSTM.BACKWARD:
                            while curIndex < length and message[curIndex] == AlgorithmToSTM.BACKWARD:
                                curIndex += 1
                            commands_len.append(curIndex - index)
                            commands.append([("S" + str(int(((curIndex - index) * BACKWARD_DISTANCE)-8)).rjust(4, '0') + BACKWARD_ANGLE).encode()])
                            index = curIndex
                        else:
                            commands.append(AlgorithmToSTM.MESSAGES[message[index]])
                            for _ in AlgorithmToSTM.MESSAGES[message[index]]:
                                commands_len.append(1)
                            index += 1
                    
                    # Passing the truncated commands to STM and Android.
                    num = 0
                    for command in commands:
                        index, length = 0, len(command)
                        while index < length:
                            if self.stm_ready_to_recv.value == 1:
                                if self.mode.value == 1:
                                    print("[Main] - Send Android")
                                    self.to_android_message_queue.put_nowait(self.format_message(AND_HEADER + STM_HEADER, STMToAndroid.DONE + str(commands_len[num]).encode()))
                                self.stm_ready_to_recv.value = 0
                                self.stm.send(command[index])
                                num, index = num + 1, index + 1
                        
                        # Stall until STM completes the movement.
                        while self.stm_ready_to_recv.value != 1:
                            continue

                        print("[Main] STM Completed one move.")
                    
                    # Finish one entire movement set, if on Exploration mode -> Take picture time.
                    if self.mode.value == 1:
                        if self.image_process is None:
                            print('[Main] Image processing is not turned on')
                            continue                                
                        image = self.take_picture()
                        print('[Main] - RPI Picture Taken')
                        self.image_queue.put_nowait([image, "Photo Time"])
                else:
                    if message not in STM_MOVESET.MESSAGES:
                        print(f"[Main] STM Command not recognised {message}")
                        continue
                    self.stm_ready_to_recv.value = 0
                    self.stm.send(message)

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
        self.stm.disconnect()

        # Reconnect android
        self.stm.connect()

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
            camera = PiCamera(resolution=(IMAGE_WIDTH, IMAGE_HEIGHT))
            camera.rotation = 0
            # camera.brightness = 50
            camera.iso = 700
            rawCapture = PiRGBArray(camera)
            # allow the camera to warmup
            time.sleep(0.1)
            
            # grab an image from the camera
            camera.capture(rawCapture, format=IMAGE_FORMAT)
            image = rawCapture.array
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            camera.close()

            print('[Main] Time Take to take picture: ' + str(datetime.now() - start_time) + 'seconds')
        
        except Exception as error:
            print("[Main] Failed to Take Picture.")
            self.error_message(error)
        
        return image

    def image_processing(self) -> None:
        # initialize the ImageSender object with the socket address of the server
        image_sender = imagezmq.ImageSender(connect_to=self.image_processing_server)
        while True:
            try:
                if self.image_queue.empty():
                    continue
                
                no_of_tries = 0
                while no_of_tries < 4:
                    start_time = datetime.now()
                    image_message =  self.image_queue.get_nowait()
                    print("[Main] Sending Image to Server.")
                    reply = image_sender.send_image(f"RPI Image", image_message[0]).decode(FORMAT)
                    print(f'[Main] Time taken to process image: {str(datetime.now() - start_time)} seconds')

                    if reply != "-1": # Image is being detected.
                        print(f"[Main] Detected Image: {reply}")
                        # Update Android with the image detected.
                        self.to_android_message_queue.put_nowait(self.format_message(AND_HEADER + RPI_HEADER, f"TARGET/{reply}".encode(FORMAT)))
                        # Request for next moveset from Algorithm
                        self.to_algo_message_queue.put_nowait(self.format_message(RPI_HEADER, RPIToAlgorithm.REQUEST_ROBOT_NEXT))
                        self.image_count.value -= 1
                        # Exploration is done.
                        if self.image_count == 0:
                            self.to_android_message_queue.put_nowait(self.format_message(AND_HEADER + RPI_HEADER, RPIToAndroid.FINISH_EXPLORE))
                            self.end()
                        break
                    
                    no_of_tries += 1

                    if no_of_tries >= 4:
                        print("[Main] Exceeded retry amount -> time to move on.")
                        break
                    
                    # Move backwards command
                    print('[Main] Failed to detect image, retrying now.')
                    self.mode.value = 0
                    self.to_stm_message_queue.put_nowait([AlgorithmToSTM.BACKWARD])

                    # Stall until movement is done.
                    while self.stm_ready_to_recv.value != 1:
                        continue
                    
                    # Retake image and repeat.
                    time.sleep(.15)
                    image = self.take_picture()
                    print('[Main] - RPI Picture Taken')
                    self.image_queue.put_nowait([image, f'No. of Tries {no_of_tries}'])

                # Exceed number of tries -> Give up -> Move forward and request next set of movements.
                if no_of_tries != 0:
                    # Time to move forward and request next step.
                    self.mode.value = 1
                    self.to_stm_message_queue.put_nowait([AlgorithmToSTM.FORWARD] * no_of_tries)
                    self.to_algo_message_queue.put_nowait(self.format_message(RPI_HEADER, RPIToAlgorithm.REQUEST_ROBOT_NEXT))

            except Exception as error:
                print('[Main] Error - Image processing failed')
                self.error_message(error)

    def recv_from_ultrasonic(self):
        while True:
            try:
                distance = self.ultrasonic.distance()
                if distance < 20:
                    self.to_stm_message_queue.put_nowait("D|{distance}")
                    print("[Main] Ultrasonic detected that it's very near an obstacle.")
                time.sleep(1)
            except Exception as error:
                print('[Main] Error - Ultrasonic read error')
                raise error

    def format_message(self, header, message) -> dict:
        return header + message
    
    def error_message(self, message : str) -> None:
        print(f"[Error Message]: {message}")