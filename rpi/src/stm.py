import serial
from misc.config import SERIAL_PORT, BAUD_RATE, FORMAT


class STM:
    def __init__(self, serial_port=SERIAL_PORT, baud_rate=BAUD_RATE) -> None:
        self.stm = None
        self.baud_rate = baud_rate
        self.serial_port = serial_port

    def connect(self) -> None:
        retry = True
        while retry:
            try:
                print(f"[STM] Establishing Connection with STM on Serial Port: {self.serial_port} Baud Rate: {self.baud_rate}")
                self.stm = serial.Serial(port=self.serial_port, baudrate=self.baud_rate, timeout=.1)
                if self.stm is not None:
                    print(f"[STM] Established connection on Serial Port: {self.serial_port} Baud Rate: {self.baud_rate}")
                    retry = False
            except Exception as error:
                print(f"[Error] Failed to establish STM Connection: {str(error)}")
                retry = True
            print(f"[STM] Retrying STM Connection...")
    
    def disconnect(self) -> None:
        try:
            if self.stm is not None:
                self.stm.close()
                self.stm = None
                print(f"[STM] STM has been disconnected.")
        except Exception as error:
            print(f"[Error] Failed to disconnect STM: {str(error)}")

    def read(self) -> str:
        try:
            message = self.stm.readline.strip()
            print(f"[STM] Message from STM: {message}")
            return message if len(message) else None
        except Exception as error:
            print(f"[Error] Failed to read from STM: {str(error)}")

    def write(self, message) -> None:
        try:
            print(f"[STM] Message to STM: {message}")
            self.stm.write(message)
        except Exception as error:
            print(f"[Error] Failed to write to STM: {str(error)}")