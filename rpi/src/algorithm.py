import socket
from misc.config import ALGO_SOCKET_BUFFER_SIZE, WIFI_IP, PORT, FORMAT

class Algorithm:
    def __init__(self, host=WIFI_IP, port=PORT):
        print("[Algo] Initialising Algorithm Process")
        
        self.host = host
        self.port = port

        self.address = None
        self.client_socket = None
        self.server_socket = None

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"[Algo] Server Address at: {self.host}:{self.port}")
    
    # Set-up connection for Algo client.
    def connect(self):
        while True:
            try:
                print(f'[Algo] Accepting Connection to: {self.host}:{self.port}]')
                if self.client_socket is None:
                    self.client_socket, self.address = self.server_socket.accept()
                    print(f'[Algo] Connected to Algo Server at {self.host}:{self.port}')
                    break
            except Exception as error:
                print(f'[Algo] Failed to setup connection for Algorithm Server at {self.host}:{self.port}')
                self.error_message(error)
                if self.client_socket is not None:
                    self.client_socket.close()
                    self.client_socket = None
            print(f'[Algo] Retrying for a connection to {self.host}:{self.port}')

    def disconnect(self):
        try:
            if self.client_socket is not None:
                self.client_socket.close()
                self.client_socket = None
            print(f'[Algo] Disconnected Algorithm Client from Server')

        except Exception as error:
            print(f'[[Algo] Failed to disconnect Algorithm Client from Server')
            self.error_message(error)

    def disconnect_all(self):
        try:
            if self.client_socket is not None:
                self.client_socket.close()
                self.client_socket = None
            if self.server_socket is not None:
                self.server_socket.close()
                self.server_socket = None
            print(f'[Algo] Disconnected Algorithm sockets')
        except Exception as error:
            print(f'[Algo] Failed to disconnect Algorithm sockets')
            self.error_message(error)

    def recv(self):
        try:
            message = self.client_socket.recv(ALGO_SOCKET_BUFFER_SIZE).strip()
            if len(message) > 0:
                # print(f'[Algo] Receive Message from Algo Client: {message}')
                return message
            return None
        except Exception as error:
            print("[Algo] Failed to receive message from Algo Client.")
            self.error_message(error)
            raise error

    def send(self, message):
        try:
            print(f'[Algo] Message to Algo Client: {message}')
            self.client_socket.send(message)

        except Exception as error:
            print("[Algo] Failed to send to Algo Client.")
            self.error_message(error)
            raise error

    def error_message(self, message):
        print(f"[Error Message]: {message}")

if __name__ == '__main__':
    server = Algorithm()
    server.connect()
    
    while True:
        message = input("[Server] Send Message to client: ")
        server.send(message.encode(FORMAT))
        recieved = server.recv()
        if recieved is not None:
            print(f"[Server] Received message from client: {recieved}")
        