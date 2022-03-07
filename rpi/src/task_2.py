# Stuff
import time
from ctypes import c_char_p
from multiprocessing import Process, Value, Manager

# Configuration + Protocols
from misc.config import *
from misc.protocols import *
from misc.calibration import *
# Interfaces
from .stm import STM
from .android import Android
from .ultrasonic import UltraSonic

class MultiProcessing:
    """
    Handles the communication between STM, Android, Algorithm and Image Processing Server.
    """    
    def __init__(self, android_on: bool, stm_on: bool, ultrasonic_on: bool, env : str) -> None:
    
        print("[Main] __init__ Multi Processing Communication")
        self.manager = Manager()
        self.calibration = Calibration(env)
        self.start_task = Value('i', 0)
        self.task_done  = Value('i', 0)

        self.ir_data = Value('i', 0)
        self.us_data = Value('i', 0)

        self.vertical_dist = Value('i', 0)
        self.horizontal_dist = Value('i', 0)
        self.stm_ready_to_recv  = Value('i', 1) # Represent if STM is ready to receive.
        self.stm = self.android = self.ultrasonic = None

        # STM
        if stm_on:
            print("[Main] Running with STM interface.") 
            self.stm = STM()
            self.to_stm_message_queue = self.manager.Queue()
            self.recv_from_stm_process = Process(target=self.recv_from_stm, name="[STM Recv Process]")
        
        # Android
        if android_on:
            print("[Main] Running with Android interface.")  
            self.android = Android()
            self.to_android_message_queue = self.manager.Queue()
            self.recv_from_android_process = Process(target=self.recv_from_android, name="[Android Recv Process]")
            self.send_to_android_process = Process(target=self.send_to_android, name="[Android Send Process]")

        if ultrasonic_on:
            print("[Main] Running Ultrasonic interface.")
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
            #Ultra Sonic
            if self.ultrasonic is not None:
                self.recv_from_ultrasonic_process.start()
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
        print("[Main] Multi Process Communication has successfully ended.")

    # Restart all processes
    def restart_speedrun(self) -> None:
        if self.stm is not None:
            # Flush instructions & Reconnect
            while not self.to_stm_message_queue.empty():
                self.to_stm_message_queue.get_nowait()
            print("[Main] - STM Message Queue has been flushed.")
            
            self.reconnect_stm()

        self.task_done.value = 0
        self.start_task.value = 0
        self.ir_data.value = 0
        self.us_data.value = 0
        self.vertical_dist.value = 0
        self.horizontal_dist.value = 0
        self.stm_ready_to_recv.value = 1

        if self.android is not None:
            while not self.to_android_message_queue.empty():
                self.to_android_message_queue.get_nowait()
            print("[Main] Android Message Queue flushed")

        
    def check_process_alive(self) -> None:
        while True:
            try:
                # Check STM connection
                if self.stm is not None and (not self.recv_from_stm_process.is_alive() or not self.send_to_stm_process.is_alive()):
                   self.reconnect_stm()
                # Check -> Android connection
                if self.android is not None and (not self.recv_from_android_process.is_alive() or not self.send_to_android_process.is_alive()):
                    self.reconnect_android()
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
                    
                    if message.split(SLASH_SEPARATOR)[0] is AndroidToRPI.START:
                        # Time to start the Task 2.
                        self.start_task.value = 1
                        self.stm.send(STM_TASK2.FORWARD)
                        continue
                    elif message == AndroidToRPI.STOP:
                        self.restart_speedrun()
                        continue
                    else:
                        print("[Main] No Forwarding - Not supported command for Task 2 : Message from Android: {message}")

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
    2. Ultra Sonic Processes (Recv)
    """
    def recv_from_ultrasonic(self):
        while True:
            try:
                distance = self.ultrasonic.distance()
                #print(f"[Main] - Ultra Sonic distance {int(distance)}")
                self.us_data.value = int(distance)
            except Exception as error:
                print('[Main] Error - Ultrasonic read error')
                raise error
    """
    3. STM Processes (Recv, Send) and function (reconnect_stm)
    """

    """
    3.1 STM recv_from_stm
    Function: Continuously read from STM using stm.recv() routine.
    Potential Redirection: Algorithm
    """
    def recv_from_stm(self) -> (None):
        counter = 0
        IR_HEADER   = "I".encode()

        while True:
            try:
                
                stm_data = self.stm.recv()

                if stm_data is None:
                    continue
                
                stm_data = stm_data.decode(FORMAT)

                if stm_data[0] in STM_TASK2.MESSAGES:
                    # Distance Data
                    if stm_data[0] == STM_TASK2.FORWARD:
                        if counter == 0:
                            self.vertical_dist.value = int(stm_data[1:5])
                            print(f"[Main] Vertical Distance: {stm_data[1:5]}")
                        elif counter == 2:
                            self.horizontal_dist.value = int(stm_data[1:5])
                            print(f"[Main] Horizontal Distance: {stm_data[1:5]}")
                        counter += 1
                    # IR Data
                    elif stm_data[0] == IR_HEADER:
                        self.ir_data.value = int(float(stm_data[5:]))
                    else:
                        print(f"[Main] Received from STM, not handling {stm_data}")
                    self.stm_ready_to_recv.value = 1
                else:
                    print(f"[Main] STM Format not supported in Task 2 -> {stm_data}")    
            except Exception as error:
                print('[Main] STM Read Error')
                self.error_message(error)
                break

    """
    3.2 send_to_stm
    Function: Constantly Check if there's anything to send to stm by checking to_stm_message_queue
    """
    def send_to_stm(self) -> None:
        # Commands for path.
        mode = 0 

        # Stall until android starts Task 2.
        while self.start_task.value == 0:
            pass
        
        while True:
            try:
                # 0: Left + Forward
                if mode == 0:
                    if self.us_data.value >= 40:
                        continue
                    # Stop STM from moving.
                    self.stm_ready_to_recv.value = 0
                    self.stm.send(STM_TASK2.BRAKE)
                    while self.stm_ready_to_recv.value == 0:
                        pass
                    # Turn Left
                    self.stm_ready_to_recv.value = 0
                    self.stm.send(STM_TASK2.TURN_LEFT)
                    while self.stm_ready_to_recv.value == 0:
                        pass
                    # Move forward.
                    self.stm.send(STM_TASK2.FORWARD)
                    mode = 1

                elif mode == 1:
                    # Stop forward
                    if self.ir_data.value <= 40:
                        continue
                    self.stm_ready_to_recv.value = 0
                    self.stm.send(STM_TASK2.BRAKE)
                    while self.stm_ready_to_recv.value == 0:
                        pass
                     # Turn Right
                    self.stm_ready_to_recv.value = 0
                    self.stm.send(STM_TASK2.TURN_RIGHT)
                    while self.stm_ready_to_recv.value == 0:
                        pass
                     # Forward
                    mode = 2
                    self.stm.send(self.bundle_forward(self.horizontal_dist.value * 2.1))
                    #self.stm.send(STM_TASK2.FORWARD)
                    
                elif mode == 2:
                    while self.stm_ready_to_recv.value == 0:
                        pass
                     # Turn Right
                    self.stm_ready_to_recv.value = 0
                    self.stm.send(STM_TASK2.TURN_RIGHT)
                    while self.stm_ready_to_recv.value == 0:
                        pass
                    # Move forward
                    self.stm_ready_to_recv.value = 0
                    self.stm.send(self.bundle_forward(self.horizontal_dist.value))
                    mode = 3

                elif mode == 3:
                    while self.stm_ready_to_recv.value == 0:
                        pass
                    # Turn Left
                    self.stm_ready_to_recv.value = 0
                    self.stm.send(STM_TASK2.TURN_LEFT)
                    while self.stm_ready_to_recv.value == 0:
                        pass
                    self.stm.send(self.bundle_forward(self.vertical_dist.value))
                    # End of Speed Run 
                    break
                
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
        print("[Main] STM Process has been Reconnected")

    
    def bundle_forward(self, distance):
        return "Q" + str(int(distance).rjust(4, '0') + "x0000").encode()

    def error_message(self, message : str) -> None:
        print(f"[Error Message]: {message}")