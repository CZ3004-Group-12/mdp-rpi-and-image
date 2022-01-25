import socket
import threading

# Header protocol 64 bytes from client -> To absorb the next <x> bytes.
HEADER = 64
PORT = 5050
# Get our local ip-address by our host-name.
SERVER = socket.gethostbyname_ex(socket.gethostname())[-1][1]
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "DISCONNECT!"

# Accept connection from IPv4
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Binding this socket to our server address.
server.bind(ADDR)

# Handle individual client to the server, running concurrently for each client
def handle_client(conn : socket, addr):
    print(f"[NEW CONNECTION {addr} connected.")
    
    connected = True
    while connected:
        # wait till something is received from client.
        msg_length = conn.recv(HEADER).decode(FORMAT) # Decode from byte -> utf 8      
        # When we connect the first time -> Not valid message.
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            if msg == DISCONNECT_MESSAGE:
                connected = False
            print(f"[{addr}] {msg}")
            conn.send("Msg received".encode(FORMAT))
    conn.close()
def start():
    server.listen()
    print(f"[LISTENING ON] Server is listening on {SERVER}:{PORT}")
    while True:
        # We wait on this line until a new connection occurs, then we store the socket, ip address + port it came from.
        conn, addr = server.accept()
        
        # Start new thread for client.
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        
        # Substract 1 because main thread is running.
        print(f"[ACTIVE CONNECTION {threading.activeCount() - 1}")
    pass

print("[STARTING] server is starting...")
start()