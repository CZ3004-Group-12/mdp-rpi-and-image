'''
Rapsberry Pi serves as socket server, Algorithm will need a client socket script
as well to establish connection. Should be able to send and receive messages
via the server/client.
'''

import socket
from misc.config import ALGO_SOCKET_BUFFER_SIZE, WIFI_IP, PORT

class Algorithm:
    def __init__(self, host=WIFI_IP, port=PORT):
        print("[Initilise] Algorithm Process")
        self.host = host
        self.port = port

        self.address = None
        self.client_socket = None
        self.server_socket = None

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(2)
        
    def connect(self):
        while True:
            try:
                print(f'[ALGO - Establishing Connection to {self.host}:{self.port}]')
                if self.client_socket is None:
                    self.client_socket, self.address = self.server_socket.accept()
                    print(f'[ALGO - Connected to Algoritmh Server at {self.host}:{self.port}]')
                    break

            except Exception as error:
                print(f'[ALGO - Failed to connect to Algorithm Server at {self.host}:{self.port}]')
                self.error_message(error)
                if self.client_socket is not None:
                    self.client_socket.close()
                    self.client_socket = None
            
            print(f'[ALGO - Retrying for a connection to {self.host}:{self.port}]')

    def disconnect(self):
        try:
            if self.client_socket is not None:
                self.client_socket.close()
                self.client_socket = None
            
            print(f'[ALGO - Disconnected Algorithm Client from Server]')

        except Exception as error:
            print(f'[ALGO - Failed to disconnect Algorithm Client from Server]')
            self.error_message(error)

    def disconnect_all(self):
        try:
            if self.client_socket is not None:
                self.client_socket.close()
                self.client_socket = None

            if self.server_socket is not None:
                self.server_socket.close()
                self.server_socket = None

            print(f'[ALGO - Disconnected Algorithm sockets]')

        except Exception as error:
            print(f'[ALGO - Failed to disconnect Algorithm sockets]')
            self.error_message(error)

    def read(self):
        try:
            message = self.client_socket.recv(ALGO_SOCKET_BUFFER_SIZE).strip()
            if len(message) > 0:
                print(f'[FROM ALGO]: {message}')
                return message
            return None

        except Exception as error:
            print('Algorithm read failed: '+ str(error))
            raise error

    def write(self, message):
        try:
            print(f'[TO ALGO]: {message}')
            self.client_socket.send(message)

        except Exception as error:
            print('Algorithm write failed: '+ str(error))
            self.error_message(error)
            raise error

    def error_message(self, message):
        print(f"[Error Message]: {message}")