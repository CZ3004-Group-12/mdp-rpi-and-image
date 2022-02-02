'''
Rapsberry Pi serves as socket server, N7 will need a client socket script
as well to establish connection. Should be able to send and receive messages
via the server/client.
'''

# Bluetooth Status
import os
from bluetooth import *
from misc.status import *
from misc.config import ANDROID_SOCKET_BUFFER_SIZE, UUID

# UUID = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
# 00001108-0000-1000-8000-00805f9b34fb

class Android:
    def __init__(self) -> None:
        print("[Android] Initialising Android Process")
        self.server_socket = None
        self.client_socket = None
        os.system("sudo hciconfig hci0 piscan")
        self.server_socket = BluetoothSocket(RFCOMM)
        self.server_socket.bind(("", PORT_ANY))
        self.server_socket.listen(1)
        self.port = self.server_socket.getsockname()[1]
        advertise_service(
            self.server_socket, 
            'MDP_Group_12',
            service_id=UUID,
            service_classes=[UUID, SERIAL_PORT_CLASS],
            profiles=[SERIAL_PORT_PROFILE],
            protocols = [ OBEX_UUID ]
        )
        print(f'[Android] Server Bluetooth Socket: {str(self.server_socket)}')
    
    def connect(self) -> None:
        retry = True
        while retry:
            try:
                print(f"[Android] Listening on RFCOMM channel: {self.port}...")
                if self.client_socket == None:
                    self.client_socket, client_addr = self.server_socket.accept()
                    print(f"[Android] Bluetooth established connection at address: {str(client_addr)}")
                    retry = False
            except Exception as error:
                print(f"[Android] Failed to establish Bluetooth Connection: {str(error)}")
                self.disconnect_client()
                retry = True
            print(f"[Android] Retrying Bluetooth Connection...")

    def disconnect_client(self) -> None:
        try:
            if self.client_socket != None:
                self.client_socket.close()
                self.client_socket = None
        except Exception as error:	
            print(f"[Android] Fail to disconnect Client Socket: {str(error)}")

    def disconnect_server(self) -> None:
        try:
            if self.server_socket != None:
                self.server_socket.close()
                self.server_socket = None
        except Exception as error:	
            print(f"[Android] Fail to disconnect Server Socket: {str(error)}")

    def disconnect_all(self) -> None:
        self.disconnect_client()
        self.disconnect_server()

    def read(self) -> None:
        try:
            message = self.client_socket.recv(ANDROID_SOCKET_BUFFER_SIZE).strip()
            print(f'[Android] [FROM ANDROID] {message}')
            if message is None:
                return None
            if len(message) > 0:
                return message
            return None
            
        except Exception as error:
            print(f"[Android] Fail to read {str(error)}")
            raise error
      
    def write(self, message) -> None:
        try:
            print(f'[Android] [TO ANDROID] {message}')
            self.client_socket.send(message)

        except Exception as error:	
            print(f"[Android] Fail to write {str(error)}")
            raise error


# Standalone testing.
if __name__ == '__main__':
    android = Android()
    android.connect()
    try:
        while True:
            android.read()
            android.write(input(f"[Android] Send Message: "))
    except KeyboardInterrupt:
        print("[Android] Terminating the program now...")    