# Stuff
import ast
import cv2
import time
import imagezmq
from datetime import datetime
from multiprocessing import Process, Value, Manager, Queue

# Camera modules
from picamera import PiCamera
from picamera.array import PiRGBArray

# Configuration + Protocols
from misc.config import *
from misc.protocols import *
from misc.calibration import *

# Interfaces
from .stm import STM
from .android import Android
from .algorithm import Algorithm

class MultiProcessing:
    """
    Handles the communication between STM, Android, Algorithm and Image Processing Server.
    """    
    def __init__(self, image_processing_server: str, android_on: bool, stm_on: bool, algo_on: bool, env : str) -> None:
    
        print("[Main] __init__ Multi Processing Communication")
        self.manager = Manager()
        self.calibration = Calibration(env) # Set calibration mode.
        print(f"[Main] Running Environment: {env}")
        
        # Coordinates for correction.
        self.coord = self.manager.dict()
        self.coord['obstacle'] = b"0-0"
        self.coord['target'] = b"(0, 0, 0)"

        self.mode  = Value('i', 0) # 0: Manual, 1: Explore, 2: Path
        self.image_count = Value('i', 0)
        self.stm_ready_to_recv  = Value('i', 1) # Represent if STM is ready to receive.
        self.stm_indv_move_done = Value('i', 1)
        self.stm = self.android = self.algorithm = self.image_process = None

        # STM
        if stm_on:
            print("[Main] Running with STM interface.") 
            self.stm = STM(env=env)
            self.to_stm_message_queue = Queue()
            self.recv_from_stm_process = Process(target=self.recv_from_stm, name="[STM Recv Process]")
            self.send_to_stm_process = Process(target=self.send_to_stm, name = "[STM Send Process]")
        
        # Android
        if android_on:
            print("[Main] Running with Android interface.")  
            self.android = Android()
            self.to_android_message_queue = Queue()
            self.recv_from_android_process = Process(target=self.recv_from_android, name="[Android Recv Process]")
            self.send_to_android_process = Process(target=self.send_to_android, name="[Android Send Process]")

        # Algorithm
        if algo_on: 
            print("[Main] Running with Algorithm interface.") 
            self.algorithm = Algorithm()
            self.to_algo_message_queue = Queue()
            self.recv_from_algorithm_process = Process(target=self.recv_from_algorithm, name="[Algorithm Recv Process]")
            self.send_to_algorithm_process = Process(target=self.send_to_algorithm, name="[Algorithm Send Process]")

        # Image Processing
        if image_processing_server is not None:
            print("[Main] Running with Image Processing.")
            self.image_queue = Queue()
            self.image_processing_server = image_processing_server 
            self.image_process = Process(target=self.image_processing, name="[Image Process]")

    # Start all processes -> Called from main.py
    def start(self) -> None:
        try:
            # STM Instance
            if self.stm is not None:
                self.stm.connect()
                self.send_to_stm_process.start()
                self.recv_from_stm_process.start()
            
            # Algorithm Instance
            # Android Instance
            if self.android is not None:
                self.android.connect()
                # self.send_to_android_process.start()
                self.recv_from_android_process.start()

            if self.algorithm is not None:
                self.algorithm.connect()
                self.send_to_algorithm_process.start()
                self.recv_from_algorithm_process.start()


            # Image Processing.
            if self.image_processing_server is not None:
                self.image_process.start()

            print('[Main] Multi Process Communication has successfully started.')

        except Exception as error:
            print(error)
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
        print("============= [Main Restarting Exploration] =============")
        if self.stm is not None:
            # Flush instructions & Reconnect
            while not self.to_stm_message_queue.empty():
                self.to_stm_message_queue.get_nowait()
            print("[Main] STM Message Queue has been flushed.")
            self.reconnect_stm()

        if self.algorithm is not None:
            while not self.to_algo_message_queue.empty():
                self.to_algo_message_queue.get_nowait()
            print("[Main] Algorithm Message Queue has been flushed")

        if self.android is not None:
            while not self.to_android_message_queue.empty():
                self.to_android_message_queue.get_nowait()
            print("[Main] Android Message Queue has been flushed")
        
        if self.image_process is not None:
            while not self.image_queue.empty():
                self.image_queue.get_nowait()
            print("[Main] Image Queue has been flushed")
            # Reset Image detected in the Image Server.
            image = self.take_picture()
            print("[Main] Taking Picture of Restarting Exploration.")
            image_sender = imagezmq.ImageSender(connect_to=self.image_processing_server)
            image_sender.send_image(0, image)
        print("===========================================================")
        
    def check_process_alive(self) -> None:
        while True:
            try:
                # Check STM connection
                pass 
                """
                if self.stm is not None and (not self.recv_from_stm_process.is_alive() or not self.send_to_stm_process.is_alive()):
                   self.reconnect_stm()
                # Check -> Android connection
                if self.android is not None and (not self.recv_from_android_process.is_alive() or not self.send_to_android_process.is_alive()):
                    self.reconnect_android()
                # Check -> Algorithm Connection.
                if self.algorithm is not None and (not self.recv_from_algorithm_process.is_alive() or not self.send_to_algorithm_process.is_alive()):
                    self.reconnect_algorithm()
                if self.image_processing_server is not None and not self.image_process.is_alive():
                   self.image_process.terminate()
                   self.image_process = Process(target=self.image_processing, name="[Image Process]")
                   self.image_process.start()
                """
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
                    # Empty message -> Ignore.
                    if not len(message): 
                        continue
                    
                    if message in AndroidToSTM.MESSAGES:
                        # Mapping Android -> RPI <-> STM protocol.
                        if self.stm is None:
                            print("[Main] No Forwarding, as STM is not set-up.")
                            continue
                        
                        # Set to manual mode -> Manual movement from android.
                        self.mode.value = 0
                        self.to_stm_message_queue.put_nowait(AndroidToSTM.MESSAGES[message])
                        continue

                    elif message == AndroidToRPI.STOP:
                        self.restart_explore()
                        continue
                        
                    # Forward Android message to Algo
                    # AND|START/EXPLORE/(R,02,02,0)/(00,10,09,0)/(01,16,03,90)
                    message_list = message.split(SLASH_SEPARATOR)
                    if len(message_list) > 1 and message_list[0] == AndroidToRPI.START and message_list[1] == AndroidToAlgorithm.EXPLORE:
                        if self.algorithm is None:
                            print("[Main] No Forwarding, as Algo is not set-up.")
                            continue
                        # Set to explore mode
                        print("=============== [Main Starting Exploration] ===============")
                        self.mode.value = 1
                        self.image_count.value = len(message_list) - 3
                        self.to_algo_message_queue.put_nowait(ANDROID_HEADER + message)
                    else:
                        print("[Main] No Forwarding : Message from Android: {message}")

            except Exception as error:
                # Peer has reset bluetooth network -> Restart now.
                print("[Main] Process of reading android has failed")
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

                for raw in raw_message.split(MESSAGE_SEPARATOR):
                    
                    message = raw.split(SLASH_SEPARATOR)

                    # MOVEMENTS/10-9/B,B,B,FL,F,F,F,F,F,FL,B,B,F,F,F,BR,F,F,F
                    if message[0] in AlgorithmToSTM.MESSAGES:
                        if self.stm is None:
                            print("[Main] No forwarding, as STM is not set-up.")
                            continue
                        # MOVEMENTS
                        if message[0] == AlgorithmToSTM.MOVEMENTS:
                            self.coord['obstacle'] = message[1]
                            print(f"[Main] Current Target Obstacle: {self.coord['obstacle']}")
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
                            self.coord['target'] = message[-1]
                            # Relay raw message to android team.
                            self.to_android_message_queue.put_nowait(AND_HEADER + ALGORITHM_HEADER + raw)
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

        # Terminate all Algorithm process.
        self.recv_from_algorithm_process.terminate()
        self.send_to_algorithm_process.terminate()
        self.algorithm.disconnect()
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
                     
                    if message not in STM_PROTOCOL.MESSAGES:
                        print(f"[Main] Command is not recognised under STM protocol: {message} Please try again.")
                        continue
                    
                    # STM is ready to receive message.
                    if message == STM_PROTOCOL.DONE:
                        self.stm_ready_to_recv.value = 1
                        print(f"[Main] Receive from STM: {message}")
                    else:
                        print(f"[Main] Doesn't match anything: received from STM: {message}")

            except Exception as error:
                print('[Main] STM Read Error')
                self.error_message(error)
                break

            # Set some delay between reading buffer.
            time.sleep(0.01)

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
                
                self.stm_indv_move_done.value = 0
                message = self.to_stm_message_queue.get_nowait()
                print(f"[Main] Raw Message from STM's MQ: {message}")

                # E.g. Movement message -> [B, B, BR, F]
                if isinstance(message, list):
                    
                    commands, commands_len = [], []
                    index, msg_len = 0, len(message)
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
                            # For BR, BL, FR, FL -> Instant map no need for bundle.
                            if message[index] not in self.calibration.calibration_map:
                                print(f"[Main] Message not recognised for STM moveset: {message[index]}")
                                break
                            commands.append(self.calibration.calibration_map[message[index]])
                            commands_len.append(1)
                            index += 1

                    # Passing the truncated commands to STM and Android.
                    # commands = [[Sxxxxxx], [Dxxx, Sxxx]]
                    print(f"[Main] Converted commands: {commands}")
                    for index, command in enumerate(commands):
                        
                        # Send command len to android.
                        if self.mode.value == 1:
                            self.to_android_message_queue.put_nowait(AND_HEADER + STM_HEADER + STMToAndroid.DONE + str(commands_len[index]).encode())
                        
                        # Send bundled instruction like BR is actually Turn right then Reverse.
                        for i in range(len(command)):
                            # Stall until previous command is executed and received call back.
                            while self.stm_ready_to_recv.value != 1:
                                continue
                            self.stm_ready_to_recv.value = 0
                            time.sleep(0.25)
                            self.stm.send(command[i])
                        # Stall until STM completes the last movement.
                        while self.stm_ready_to_recv.value != 1:
                            continue
                            
                        print("[Main] STM Completed one move.")

                    # Finish one entire movement set, if on Exploration mode -> Take picture time.
                    if self.mode.value == 1:
                        if self.image_processing_server is None:
                            print('[Main] Image processing is not turned on')
                            self.to_algo_message_queue.put_nowait(RPI_HEADER + RPIToAlgorithm.REQUEST_ROBOT_NEXT + RPIToAlgorithm.NIL)
                            continue                                
                        image = self.take_picture()
                        print(f'[Main] First Picture Taken -> STM completed one movement.')
                        self.image_queue.put_nowait([image, f"{self.image_count.value}"])
                    else:
                        print("[Main] Mode is Manual")
                else:
                    # For raw messages -> most likely for  Straight / Reverse.
                    commands = []
                    if message[0] == "W".encode():
                        commands = [self.calibration.STRAIGHT_F_I, self.calibration.STRAIGHT_F_P, message]
                    else:
                        commands = [self.calibration.STRAIGHT_R_I, self.calibration.STRAIGHT_R_P, message]
                    
                    for msg in commands:
                        while self.stm_ready_to_recv.value != 1:
                            continue
                        self.stm_ready_to_recv.value = 0
                        time.sleep(0.25)
                        self.stm.send(msg)
                self.stm_indv_move_done.value = 1  

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
        self.stm.disconnect()
        self.stm.connect()
        # Recreate all processes as Process cant be restart
        self.recv_from_stm_process = Process(target=self.recv_from_stm, name="[STM Recv Process]")
        self.send_to_stm_process = Process(target=self.send_to_stm, name="[STM Send Process]")
        self.recv_from_stm_process.start()
        self.send_to_stm_process.start()
        self.stm_ready_to_recv.value = 1
        self.stm_indv_move_done.value = 1
        print("[Main] STM Process has been Reconnected")

    """
    4. RPI Functions
    """
    def take_picture(self) -> None:
        try:
            # start_time = datetime.now()
            # initialize the camera and grab a reference to the raw camera capture
            camera = PiCamera(resolution=(IMAGE_WIDTH, IMAGE_HEIGHT))
            camera.rotation = 0
            # camera.brightness = 50
            camera.iso = 700
            rawCapture = PiRGBArray(camera)
            # allow the camera to warmup
            time.sleep(0.2)
            # grab an image from the camera
            camera.capture(rawCapture, format=IMAGE_FORMAT)
            image = rawCapture.array
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            camera.close()
            #print('[Main] Time Take to take picture: ' + str(datetime.now() - start_time) + 'seconds')
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
                
                # Each image has 4 tries.
                rebound = 0
                image_message =  self.image_queue.get_nowait()
                for cur_try in range(4):
                    start_time = datetime.now()
                    print(f"[Main] Sending Image to Server -> Tries: {cur_try + 1}")
                    reply = image_sender.send_image(image_message[1], image_message[0]).decode(FORMAT)
                    print(f'[Main] Time taken to process image: {str(datetime.now() - start_time)} seconds')
                    
                    if reply == "NIL":
                        # Move backwards command
                        print('[Main] Failed to detect image, retrying now.')
                        self.mode.value = 0
                        self.stm_indv_move_done.value = 0
                        self.to_stm_message_queue.put_nowait([COMMAND_LIST.B])

                        # Stall until movement is done.
                        while self.stm_indv_move_done.value != 1:
                            continue
                        
                        # Retake image and repeat.
                        rebound = cur_try + 1
                        image = self.take_picture()
                        image_message = [image, f"{self.image_count.value}"]

                    else:
                        image_id, distance = reply.split("/")
                        distance = float(distance)
                        print(f"[Main] Detected Image: {image_id}, Distance away: {distance}")
                        # Update Android with the image detected.
                        self.to_android_message_queue.put_nowait(AND_HEADER + RPI_HEADER + f"TARGET/{image_id}".encode(FORMAT))
                        self.image_count.value -= 1
                        # Exploration is done -> Thats the final picture.
                        if self.image_count.value == 0:
                            self.to_android_message_queue.put_nowait(AND_HEADER + RPI_HEADER + RPIToAndroid.FINISH_EXPLORE)
                            self.restart_explore()
                            break

                        # Move forward to offset the difference.
                        if distance >= self.calibration.MINUS_UNIT:
                            # Move Forward with the distance.
                            self.stm_indv_move_done.value = 0
                            self.to_stm_message_queue.put_nowait(self.calibration.bundle_movement_raw(0, distance / 21))

                        # Stall until movement is done.
                        while self.stm_indv_move_done.value != 1:
                            continue
                        
                        # Request for next moveset from Algorithm
                        self.to_algo_message_queue.put_nowait(RPI_HEADER + RPIToAlgorithm.REQUEST_ROBOT_NEXT + RPIToAlgorithm.NIL)
                        rebound = 0
                        self.mode.value = 1
                        break

                # Gives up on detecting image -> Forward again.
                if rebound != 0:
                    # Can't detect the final image -> Just stop.
                    if self.image_count.value == 1:
                        self.to_android_message_queue.put_nowait(AND_HEADER + RPI_HEADER + RPIToAndroid.FINISH_EXPLORE)
                        self.restart_explore()
                        break
                    # Time to move forward and request next step.
                    self.mode.value = 0
                    self.image_count.value -= 1
                    self.stm_indv_move_done.value = 0
                    self.to_stm_message_queue.put_nowait([COMMAND_LIST.F] * rebound)
                    # Stall until movement is done.
                    while self.stm_indv_move_done.value != 1:
                        continue
                    self.mode.value = 1
                    self.to_algo_message_queue.put_nowait(RPI_HEADER + RPIToAlgorithm.REQUEST_ROBOT_NEXT + RPIToAlgorithm.NIL)
       
            except Exception as error:
                print('[Main] Error - Image processing failed')
                self.error_message(error)
                    
    def error_message(self, message : str) -> None:
        print(f"[Error Message]: {message}")