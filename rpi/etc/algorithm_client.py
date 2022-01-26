"""
Testing Algorithm Socket Only - Not used in production.
"""
import queue
import socket
import threading
from misc.config import FORMAT, ALGO_SOCKET_BUFFER_SIZE, WIFI_IP, PORT

class AlgoClient:

    def __init__(self) -> None:
        print("[Algo Client] Initilising Algo Client")
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((WIFI_IP, PORT))
        self.incoming_message_queue = queue.Queue()
        self.message_sender = threading.Thread(target=self.message_sender_thread)
        self.message_receiver = threading.Thread(target=self.message_receiver_thread)
        self.printer = threading.Thread(target=self.print_messages)
        print("[Algo Client] Algo Client Receiver Thread started")
        self.message_receiver.start()
        print("[Algo Client] Algo Client Sender Thread started")
        self.message_sender.start()
        self.printer.start()

    def message_sender_thread(self) -> None:
        # We want to encode into bytes.
        while True:
            msg = input("[Algo Client] Message to server: ")
            message = msg.encode(FORMAT)
            # Pad to Socket buffer size
            #message += (ALGO_SOCKET_BUFFER_SIZE - len(message)) * b' ' 
            self.client.send(message)
            print(f"[Algo Client] Message Sent: {msg}")

    def message_receiver_thread(self) -> None:
        while True:
            message = self.client.recv(ALGO_SOCKET_BUFFER_SIZE).decode(FORMAT)
            self.incoming_message_queue.put(message)
    
    def print_messages(self) -> None:
        while True:
            try:
                msg = self.incoming_message_queue.get_nowait()
                print(msg)
            except queue.Empty:
                pass

# Standalone testing.
if __name__ == '__main__':
    AlgoClient()