import socket

# Header protocol 64 bytes from client -> To absorb the next <x> bytes.
HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "DISCONNECT!"
SERVER = "192.168.86.54"
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

def send(msg):
    # We want to encode into bytes.
    message = msg.encode(FORMAT)
    msg_length = len(message)

    # Encode into message length
    send_length = str(msg_length).encode(FORMAT)

    # Pad to 64 bytes
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)
    print(client.recv(2048))


client.send("Hello im here")