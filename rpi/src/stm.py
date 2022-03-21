
import time
import serial
from misc.protocols import STM_PROTOCOL
from misc.config import SERIAL_PORT, BAUD_RATE

class STM:
    def __init__(self, serial_port=SERIAL_PORT, baud_rate=BAUD_RATE, env:str = None) -> None:
        self.env = env
        self.flip = 0
        self.stm = None
        self.baud_rate = baud_rate
        self.serial_port = serial_port[self.flip]

    # Establish connection with STM Board
    def connect(self) -> None:
        retry = True
        while retry:
            try:
                print(f"[STM] Establishing Connection with STM on Serial Port: {self.serial_port} Baud Rate: {self.baud_rate}")
                self.stm = serial.Serial(port=self.serial_port, baudrate=self.baud_rate, timeout=None)
                if self.stm is not None:
                    print(f"[STM] Established connection on Serial Port: {self.serial_port} Baud Rate: {self.baud_rate}")
                    #if self.env == 'g-outdoor':
                        #self.send(b'G0104x0100')
                        #self.recv()
                    retry = False
            except IOError as error:
                print(f"[Error] Failed to establish STM Connection: {str(error)}")
                # Alternate port due to potential port flip due to failed connection.
                if error.errno == 2:
                    self.flip ^= 1
                    self.serial_port = SERIAL_PORT[self.flip]
                    print(f"[STM] Switching port to {self.serial_port} due to Port Flip.")
                    time.sleep(1)
                retry = True
            if retry:
                print(f"[STM] Retrying STM Connection...")
    
    def disconnect(self) -> None:
        try:
            if self.stm is not None:
                self.stm.close()
                self.stm = None
                print(f"[STM] STM has been disconnected.")
        except Exception as error:
            print(f"[Error] Failed to disconnect STM: {str(error)}")

    def recv(self) -> str:
        try:
            if self.stm.inWaiting() > 0:
                if self.stm.inWaiting() >= 10:
                    message = self.stm.read(10).strip()
                    return message
                else:
                    print(f"[!!!!!!] Buffer less than 10 bytes -> {self.stm.read(self.stm.inWaiting())}")
            return None
        except Exception as error:
            print(f"[Error] Failed to recieve from STM: {str(error)}")

    def send(self, message) -> None:
        try:
            print(f"[STM] Message to STM: {message}")
            self.stm.write(message)
        except Exception as error:
            print(f"[Error] Failed to send to STM: {str(error)}")

# Standalone testing.
if __name__ == '__main__':
    stm = STM()
    stm.connect()
    try:
        while True:
            message_to_send = input(f"[STM] Send Message: ")
            stm.send(message_to_send.rstrip().encode())
            stm.recv()
    except KeyboardInterrupt:
        print("[STM] Terminating the program now...")    