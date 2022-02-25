'''
Rapsberry Pi serves as socket server, Algorithm will need a client socket script
as well to establish connection. Should be able to send and receive messages
via the server/client.
'''

import socket
from misc.config import ALGO_SOCKET_BUFFER_SIZE, WIFI_IP, FORMAT
from misc.protocols import STM_MOVESET
# FORMAT = "UTF-8"
# ALGO_SOCKET_BUFFER_SIZE = 1024
# WIFI_IP = "192.168.68.110"
# PORT = 5050

class STM:
    def __init__(self, host=WIFI_IP, port=5051):
        print("[STM] Initialising Algorithm Process")
        
        self.host = host
        self.port = port

        self.address = None
        self.client_socket = None
        self.server_socket = None

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print(f"[STM] Server Address at: {self.host}:{self.port}")

    def connect(self):
        while True:
            try:
                print(f'[STM] Accepting Connection to: {self.host}:{self.port}]')
                if self.client_socket is None:
                    self.client_socket, self.address = self.server_socket.accept()
                    print(f'[STM] Connected to STM Server at {self.host}:{self.port}')
                    self.send(STM_MOVESET.SETUP_I)
                    self.send(STM_MOVESET.SETUP_P)
                    break

            except Exception as error:
                print(f'[STM] Failed to setup connection for Algorithm Server at {self.host}:{self.port}')
                self.error_message(error)
                if self.client_socket is not None:
                    self.client_socket.close()
                    self.client_socket = None
            
            print(f'[STM] Retrying for a connection to {self.host}:{self.port}')

    def disconnect(self):
        try:
            if self.client_socket is not None:
                self.client_socket.close()
                self.client_socket = None
            print(f'[STM] Disconnected Algorithm Client from Server')

        except Exception as error:
            print(f'[[STM] Failed to disconnect Algorithm Client from Server')
            self.error_message(error)

    def disconnect_all(self):
        try:
            if self.client_socket is not None:
                self.client_socket.close()
                self.client_socket = None

            if self.server_socket is not None:
                self.server_socket.close()
                self.server_socket = None

            print(f'[STM] Disconnected Algorithm sockets')

        except Exception as error:
            print(f'[STM] Failed to disconnect Algorithm sockets')
            self.error_message(error)

    def recv(self):
        try:
            message = self.client_socket.recv(ALGO_SOCKET_BUFFER_SIZE).strip()
            if len(message) > 0:
                print(f'[STM] Receive Message from STM Client: {message}')
                return message
            return None

        except Exception as error:
            print("[STM] Failed to receive message from STM Client.")
            self.error_message(error)
            raise error

    def send(self, message):
        try:
            print(f'[STM] Message to STM Client: {message}')
            self.client_socket.send(message)

        except Exception as error:
            print("[STM] Failed to send to STM Client.")
            self.error_message(error)
            raise error

    def error_message(self, message):
        print(f"[Error Message]: {message}")

if __name__ == '__main__':
    server = STM()
    server.connect()
    
    while True:
        message = input("[Server] Send Message to client: ")
        server.send(message.encode(FORMAT))
        recieved = server.recv()
        if recieved is not None:
            print(f"[Server] Received message from client: {recieved}")
        