"""
Testing Algorithm Socket Only - Not used in production.
"""
import socket
from misc.config import FORMAT, ALGO_SOCKET_BUFFER_SIZE, WIFI_IP, PORT

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((WIFI_IP, PORT))

def send(msg):
    # We want to encode into bytes.
    message = msg.encode(FORMAT)
    # Pad to Socket buffer size
    message += (ALGO_SOCKET_BUFFER_SIZE - len(message)) * b' ' 
    client.send(message)
    print(client.recv(ALGO_SOCKET_BUFFER_SIZE))

# Standalone testing.
if __name__ == '__main__':
    print("[Starting up Algo client]")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((WIFI_IP, PORT))
    try:
        while True:
            send(input("[Send RPI Message from Algo]: "))
    except KeyboardInterrupt:
        print("Terminating the program now...")    