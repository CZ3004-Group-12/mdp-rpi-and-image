# Stuff
import time
from multiprocessing import Process, Value, Manager

# Configuration + Protocols
from misc.config import *
from misc.protocols import *
from misc.calibration import *
# Interfaces
from .stm import STM
from .android import Android
from .ultrasonic import UltraSonic

class TASK2:
    DONE    = "0000000000".encode()

class SpeedRun:
    """
    Handles the communication between STM, Android, Algorithm and Image Processing Server.
    """    
    def __init__(self, android_on: bool, stm_on: bool, ultrasonic_on: bool, env : str) -> None:
    
        print("[Main] __init__ Multi Processing Communication")
        self.manager = Manager()
        self.start_task = Value('i', 0)
        
        self.stm = self.android = self.ultrasonic = None

        # STM
        if stm_on:
            print("[Main] Running with STM interface.") 
            self.stm = STM()
            self.to_stm_message_queue = self.manager.Queue()
            self.recv_from_stm_process = Process(target=self.recv_from_stm, name="[STM Recv Process]")
            self.send_to_stm_process = Process(target=self.send_to_stm, name = "[STM Send Process]")

        # Android
        if android_on:
            print("[Main] Running with Android interface.")  
            self.android = Android()
            self.to_android_message_queue = self.manager.Queue()
            self.recv_from_android_process = Process(target=self.recv_from_android, name="[Android Recv Process]")

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
        self.start_task.value = 0

        if self.stm is not None:
            # Flush instructions & Reconnect
            self.recv_from_stm_process.terminate()
            self.send_to_stm_process.terminate()
        
            while not self.to_stm_message_queue.empty():
                self.to_stm_message_queue.get_nowait()
            
            print("[Main] - STM Message Queue has been flushed.")
            self.recv_from_stm_process = Process(target=self.recv_from_stm, name="[STM Recv Process]")
            self.send_to_stm_process = Process(target=self.send_to_stm, name="[STM Send Process]")
            self.recv_from_stm_process.start()
            self.send_to_stm_process.start()

        if self.android is not None:
            while not self.to_android_message_queue.empty():
                self.to_android_message_queue.get_nowait()
            print("[Main] Android Message Queue flushed")

        
    def check_process_alive(self) -> None:
        while True:
            try:
                # Check STM connection
                if self.stm is not None and (not self.recv_from_stm_process.is_alive() or not self.send_to_stm_process.is_alive()):
                   pass
                   # self.reconnect_stm()
                # Check -> Android connection
                if self.android is not None and not self.recv_from_android_process.is_alive():
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
                    
                    message_list = message.split(SLASH_SEPARATOR)
                    
                    # START/EXPLORE/
                    print(message_list, message_list[0],AndroidToRPI.START )
                    if message_list[0] == AndroidToRPI.START:
                        # Time to start the Task 2.
                        self.start_task.value = 1
                        self.to_stm_message_queue.put_nowait("START")
                    elif message == AndroidToRPI.STOP:
                        self.restart_speedrun()
                        continue
                    else:
                        print(f"[Main] No Forwarding - Not supported command for Task 2 : Message from Android: {message}")

            except Exception as error:
                # Peer has reset bluetooth network -> Restart now.
                print("[Main] Process of reading android has failed")
                self.error_message(error)
                self.reconnect_android()
    
    """
    1.3 Reconnect to android 
    Function: Terminate android send/recv process and recreate them.
    """  
    def reconnect_android(self) -> None:
        print("[Main] Disconnecting Android Process.")

        # Terminate all Android process.
        self.recv_from_android_process.terminate()
        print("[Main] Android send/recv processes has been terminated ")

        # Close all Android bluetooth sockets.
        self.android.disconnect_client()

        # Reconnect android
        self.android.connect()

        # Recreate all processes as Process cant be restart
        self.recv_from_android_process = Process(target=self.recv_from_android, name="[Android Recv Process]")
        self.recv_from_android_process.start()
        print("[Main] Android send/recv processes has been reconnected.")

 

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
                
                stm_data = self.stm.recv()

                if stm_data is None:
                    continue

                if stm_data == TASK2.DONE:
                    # Finish path finding.
                    self.android.send(AND_HEADER + RPI_HEADER + RPIToAndroid.FINISH_PATH)
                    break
                else:
                    print(f"[Main] Received from STM, not handling {stm_data}")
                    # STM Done some command
            except Exception as error:
                print('[Main] STM Read Error')
                self.error_message(error)
                break

    """
    3.2 send_to_stm
    Function: Constantly Check if there's anything to send to stm by checking to_stm_message_queue
    """
    def send_to_stm(self) -> None:

        # Stall until android starts Task 2.
        while self.start_task.value == 0:
            continue

        while True:
            try:
                if not self.to_stm_message_queue.empty():
                    raw_msg = self.to_stm_message_queue.get_nowait()
                    print(f"[Main] Raw Message from STM MQ: {raw_msg}")
                    # Ultrasonic Data -> Send to STM
                    if raw_msg[0] == "U":
                        self.stm.send(raw_msg.encode(FORMAT))
                    # Android send START.
                    elif raw_msg == "START":
                        self.stm.send("L0000x0000".encode(FORMAT))
                    else:
                        print(raw_msg)
                
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
        print("[Main] STM Process has been Reconnected")

    """
    2. Ultra Sonic Processes (Recv)
    """
    def recv_from_ultrasonic(self):
        while True:
            try:
                while self.start_task.value == 0:
                    continue
                distance = self.ultrasonic.distance()
                self.to_stm_message_queue.put_nowait(self.us_data_converter(int(distance)))
                # Time delay 100ms.
                time.sleep(0.1)

            except Exception as error:
                print('[Main] Error - Ultrasonic read error')
                raise error
    
    def us_data_converter(self, us_data):
        return "U0000x" + str(us_data).rjust(4, '0')

    def error_message(self, message : str) -> None:
        print(f"[Error Message]: {message}")