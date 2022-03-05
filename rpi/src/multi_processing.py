import ast
import cv2
import time
import imagezmq
from misc.config import *
from misc.protocols import *
from misc.calibration import *

from picamera import PiCamera
from picamera.array import PiRGBArray

from datetime import datetime
from ctypes import c_char_p
from multiprocessing import Process, Value, Manager

from .stm import STM
from .android import Android
from .algorithm import Algorithm
from .ultrasonic import UltraSonic

class MultiProcessing:
    """
    Handles the communication between STM, Android, Algorithm and Image Processing Server.
    """    
    def __init__(self, image_processing_server: str, android_on: bool, stm_on: bool, algo_on: bool, ultrasonic_on: bool, env : str) -> None:
    
        print("[Main] __init__ Multi Processing Communication")
        self.manager = Manager()
        
        self.mode  = Value('i', 0) # 0: Manual, 1: Explore, 2: Path
        self.image_count = Value('i', 0)
        self.calibration = Calibration(env)
        self.stm_ready_to_recv  = Value('i', 1)
        self.cur_obstacle_coord = Value(c_char_p, b"0-0")
        self.target_position_coord = Value(c_char_p, b"(0, 0, 0)")
        self.stm = self.android = self.algorithm = self.image_process = self.ultrasonic = None

        # STM
        if stm_on:
            print("[Main] Running with STM") 
            self.stm = STM()
            self.to_stm_message_queue = self.manager.Queue()
            self.recv_from_stm_process = Process(target=self.recv_from_stm, name="[STM Recv Process]")
            self.send_to_stm_process = Process(target=self.send_to_stm, name = "[STM Send Process]")
        
        # Android
        if android_on:
            print("[Main] Running with Android")  
            self.android = Android()
            self.to_android_message_queue = self.manager.Queue()
            self.recv_from_android_process = Process(target=self.recv_from_android, name="[Android Recv Process]")
            self.send_to_android_process = Process(target=self.send_to_android, name="[Android Send Process]")

        # Algorithm
        if algo_on: 
            print("[Main] Running with Algorithm") 
            self.algorithm = Algorithm()
            self.to_algo_message_queue = self.manager.Queue()
            self.recv_from_algorithm_process = Process(target=self.recv_from_algorithm, name="[Algorithm Recv Process]")
            self.send_to_algorithm_process = Process(target=self.send_to_algorithm, name="[Algorithm Send Process]")

        # Image Processing
        if image_processing_server is not None:
            print("[Main] Running with Image Processing")
            self.image_queue = self.manager.Queue()
            self.image_processing_server = image_processing_server 
            self.image_process = Process(target=self.image_processing, name="[Image Process]")

        if ultrasonic_on:
            print("[Main] Running ultrasonic")
            self.ultrasonic = UltraSonic()
            self.recv_from_ultrasonic_process = Process(target=self.recv_from_ultrasonic, name="[Ultra Sonic Recv Process]")

    # Start all processes -> Called from main.py
    def start(self) -> None:
        try:
            # STM Instance
            if self.stm is not None:
                self.stm.connect()
                self.send_to_stm_process.start()
                self.recv_from_stm_process.start()
            # Android Instance
            if self.android is not None:
                self.android.connect() 
                self.send_to_android_process.start()
                self.recv_from_android_process.start()
            # Algorithm Instance
            if self.algorithm is not None:
                self.algorithm.connect()
                self.send_to_algorithm_process.start()
                self.recv_from_algorithm_process.start()
            # Image Processing.
            if self.image_processing_server is not None:
                self.image_process.start()
            #Ultra Sonic
            if self.ultrasonic is not None:
                self.recv_from_ultrasonic_process.start()
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

    # Restart all processes
    def restart_explore(self) -> None:
        
        if self.stm is not None:
            # Flush instructions & Reconnect
            while not self.to_stm_message_queue.empty():
                self.to_stm_message_queue.get_nowait()
            print("[Main] - STM Message Queue has been flushed.")
            self.reconnect_stm()

        if self.algorithm is not None:
            while not self.send_to_algorithm_process.empty():
                self.send_to_algorithm_process.get_nowait()
            print("[Main] Algorithm Message Queue flushed")

        if self.android is not None:
            while not self.to_android_message_queue.empty():
                self.to_android_message_queue.get_nowait()
            print("[Main] Android Message Queue flushed")

        if self.image_process is not None:
            while not self.image_queue.empty():
                self.image_queue.get_nowait()
            print("[Main] Image Queue flushed")
            image = self.take_picture()
            image_sender = imagezmq.ImageSender(connect_to=self.image_processing_server)
            image_sender.send_image(0, image)

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
                        self.restart_explore()
                        continue
                        
                    # Forward Android message to Algo
                    message_list = message.split(COMMAND_SEPARATOR)
                    if len(message_list) > 1 and message_list[0] == AndroidToRPI.START and message_list[1] == AndroidToAlgorithm.EXPLORE:
                        if self.algorithm is None:
                            print("[Main] No Forwarding, as Algo is not set-up.")
                            continue
                        # Set to explore mode
                        self.mode.value = 1
                        self.image_count.value = len(message_list) - 3
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
                    
                    message = message.split(COMMAND_SEPARATOR)

                    # MOVEMENTS/10-9/B,B,B,FL,F,F,F,F,F,FL,B,B,F,F,F,BR,F,F,F
                    if message[0] in AlgorithmToSTM.MESSAGES:

                        if self.stm is None:
                            print("[Main] No forwarding, as STM is not set-up.")
                            continue
                        # MOVEMENTS
                        if message[0] == AlgorithmToSTM.MOVEMENTS:
                            self.cur_obstacle_coord.value = message[1]
                            print(f"[Main] - Current Target Obstacle: {message[1]}")
                            self.to_stm_message_queue.put_nowait(message[2].split(COMMA_SEPARATOR))
                        else:    
                            print("[Main] Algorithm To STM Command Type not recognised.")
                    # ROBOT/10-9/(11.0, 2.0, -90)/(10.0, 2.0, -90)/(9.0, 2.0, -90)/(12.0, 5.0, 0)/(12.0, 6.0, 0)/(12.0, 7.0, 0)/(12.0, 8.0, 0)/(12.0, 9.0, 0)/(12.0, 10.0, 0)/(9.0, 13.0, 90)/(10.0, 13.0, 90)/(11.0, 13.0, 90)/(10.0, 13.0, 90)/(9.0, 13.0, 90)/(8.0, 13.0, 90)/(11.0, 16.0, 180)/(11.0, 15.0, 180)/(11.0, 14.0, 180)/(11.0, 13.0, 180)
                    elif message[0] in AlgorithmToAndroid.MESSAGES:
                        if self.android is None:
                            print("[Main] No forwarding, as Android is not set-up.")
                            continue
                        if message[0] == AlgorithmToAndroid.ROBOT:
                            # Keept track of the target position, for calibration purposes.
                            self.target_position_coord.value = message[2].split(b'/')[-1]
                            # Relay raw message to android team.
                            self.to_android_message_queue.put_nowait(self.format_message(AND_HEADER + ALGORITHM_HEADER, message))
                    # Take picture of obstacle manually.
                    elif message[0] == AlgorithmToRPI.OBSTACLE:
                            image = self.take_picture()
                            print('[Main] - RPI Picture Taken')
                            self.image_queue.put_nowait([image, message[1]])
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
                    if message is None or message is STM_PROTOCOL.SETUP_DONE:
                        continue
                    # 
                    if message not in STM_PROTOCOL.MESSAGES:
                        print("[Main] Command is not recognised under STM protocol. Please try again.")
                        continue
                    # STM is ready to receive message.
                    if message == STM_PROTOCOL.DONE:
                        time.sleep(.05)
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
                # E.g. Movement message -> [B, B, BR, F]
                if isinstance(message, list):
                    commands, commands_len = [], []
                    num, index, msg_len = 0, 0, len(message)
                    # Truncating and mapping movement from [B, B, B, BR] -> [[Sxxxxxx], [Dxxx, Sxxx]]
                    # Reason for commands_len -> need send Android how many unit of movement instead.
                    while index < msg_len:
                        curIndex = index
                        if message[index] == COMMAND_LIST.F:
                            while curIndex < msg_len and message[curIndex] == COMMAND_LIST.F:
                                curIndex += 1
                            commands_len.append(curIndex - index)
                            commands.append(self.calibration.bundle_movement(0, curIndex - index))
                            index = curIndex
                        elif message[index] == COMMAND_LIST.B:
                            while curIndex < msg_len and message[curIndex] == COMMAND_LIST.B:
                                curIndex += 1
                            commands_len.append(curIndex - index)
                            commands.append(self.calibration.bundle_movement(180, curIndex - index))
                            index = curIndex
                        else:
                            actual_instruction = self.calibration.calibration_map[message[index]]
                            index += 1
                            commands_len.append(1)
                            commands.append(actual_instruction)

                    # Passing the truncated commands to STM and Android.
                    for command in commands:
                        index = 0
                        if self.mode.value == 1:
                            print("[Main] - Send Android")
                            self.to_android_message_queue.put_nowait(self.format_message(AND_HEADER + STM_HEADER, STMToAndroid.DONE + str(commands_len[num]).encode()))
                            num += 1
                        # Send bundled instruction like BR is actually Turn right then Reverse.
                        while index < len(command):
                            if self.stm_ready_to_recv.value == 1:
                                self.stm_ready_to_recv.value = 0
                                self.stm.send(command[index])
                                index += 1
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
                        self.image_queue.put_nowait([image, f"detect_image/{self.image_count.value}"])
                else:
                    #if message not in STM_PROTOCOL.MESSAGES:
                     #   print(f"[Main] STM Command not recognised {message}")
                    #  continue
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
                    reply = image_sender.send_image(image_message[1], image_message[0]).decode(FORMAT)
                    print(f'[Main] Time taken to process image: {str(datetime.now() - start_time)} seconds')
                    # Image is detected -> Time to notify Android + recalibration.
                    if reply != "-1": 
                        image_id, distance = reply.split("/")
                        print(f"[Main] Detected Image: {image_id}, Distance away: {distance}")
                        # Update Android with the image detected.
                        self.to_android_message_queue.put_nowait(self.format_message(AND_HEADER + RPI_HEADER, f"TARGET/{image_id}".encode(FORMAT)))

                        # Evaluate if exploration is done.
                        self.image_count.value -= 1
                        # Exploration is done.
                        if self.image_count == 0:
                            self.to_android_message_queue.put_nowait(self.format_message(AND_HEADER + RPI_HEADER, RPIToAndroid.FINISH_EXPLORE))
                            self.restart_explore()
                            break

                        # Move Forward with the distance.
                        self.to_stm_message_queue.put_nowait(("Q" + str(int(distance) - self.calibration.MINUS_UNIT).rjust(4, '0') + self.calibration.FORWARD_ANGLE).encode())

                        # Stall until movement is done.
                        while self.stm_ready_to_recv.value != 1:
                            continue
                        
                        image = self.take_picture()
                        reply = image_sender.send_image("calibrate", image).decode(FORMAT)
                        grid_offset = reply.split("/")[1]
                        
                        # Check if it's intentional misaligned.
                        obstacle_x, obstacle_y = [int(x) for x in self.cur_obstacle_coord.value.decode(FORMAT).split("-")]
                        perceived_x, perceived_y, perceived_angle = ast.literal_eval(self.target_position_coord.value.decode(FORMAT))
                        msg_to_send = RPIToAlgorithm.REQUEST_ROBOT_NEXT + RPIToAlgorithm.NIL

                        if perceived_angle == 0 or perceived_angle == 180:
                            actual_x = obstacle_x - grid_offset if perceived_angle == 0 else obstacle_x + grid_offset
                            # Not an intentional offset by Algorithm
                            if actual_x != perceived_x:
                                msg_to_send = RPIToAlgorithm.REQUEST_ROBOT_NEXT + f"{actual_x},{perceived_y},{perceived_angle}".encode()
                        else:
                            actual_y = obstacle_y - grid_offset if perceived_angle == 90 else obstacle_y + grid_offset
                            # Intentional offset by Algorithm
                            if actual_y != perceived_y:
                                actual_coord = f"{perceived_x},{actual_y},{perceived_angle}".encode()
                                msg_to_send = RPIToAlgorithm.REQUEST_ROBOT_NEXT + actual_coord

                        # Request for next moveset from Algorithm
                        self.to_algo_message_queue.put_nowait(self.format_message(RPI_HEADER, msg_to_send))
                        break

                    no_of_tries += 1

                    if no_of_tries >= 4:
                        print("[Main] Exceeded retry amount -> time to move on.")
                        break
                    
                    # Move backwards command
                    print('[Main] Failed to detect image, retrying now.')
                    self.mode.value = 0
                    self.to_stm_message_queue.put_nowait([COMMAND_LIST.B])

                    # Stall until movement is done.
                    while self.stm_ready_to_recv.value != 1:
                        continue
                    
                    # Retake image and repeat.
                    image = self.take_picture()
                    print('[Main] - RPI Picture Taken')
                    self.image_queue.put_nowait([image, f'No. of Tries {no_of_tries}'])

                # Exceed number of tries -> Give up -> Move forward and request next set of movements.
                if no_of_tries != 0:
                    # Time to move forward and request next step.
                    self.mode.value = 1
                    self.image_count.value -= 1
                    self.to_stm_message_queue.put_nowait([COMMAND_LIST.F] * no_of_tries)
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