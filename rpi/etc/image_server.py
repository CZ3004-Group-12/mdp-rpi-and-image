import os
import cv2
from misc.config import *
from imagezmq import ImageHub
from datetime import datetime

class CustomImageHub(ImageHub):
    def send_reply(self, reply_message):
        """Sends the zmq REP reply message.
        Arguments:
          reply_message: reply message text, often just string 'OK'
        """
        reply_message = reply_message.encode('utf-8')
        self.zmq_socket.send(reply_message)


class ImageProcessingServer:
    def __init__(self):

        # initialize the ImageHub object
        self.image_hub = CustomImageHub(open_port=f"tcp://:{IMAGE_SERVER_PORT}")
        
    def start(self):

        print('\nStarted image processing server.\n')
        
        while True:
            try:
                print('Waiting for image from RPi...')

                # receive RPi name and frame from the RPi and acknowledge the receipt
                _, frame = self.image_hub.recv_image()
                print('Connected and received frame at time: ' + str(datetime.now()))
                # form image file path for saving
                raw_image_name = "Test RPI Image " + str(datetime.now())
                dir_path = os.path.dirname(os.path.realpath(__file__))
                raw_image_path = os.path.join(dir_path, raw_image_name)
                
                # save raw image
                cv2.imwrite(raw_image_path, frame)
                break

            except KeyboardInterrupt as e:
                print("Ctrl-C")
        self.end()

    def end(self):
        print('Stopping image processing server')
        self.image_hub.send_reply('Done')
        # send_reply disconnects the connection
        print('Sent reply and disconnected at time: ' + str(datetime.now()) + '\n')

# Standalone testing.
if __name__ == '__main__':
    print("[Starting up Image Server]")
    image_hub = ImageProcessingServer()
    image_hub.start()