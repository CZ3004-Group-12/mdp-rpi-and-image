
import os
import time
import cv2
from imagezmq import ImageHub
from datetime import datetime

from rpi.misc.config import *
from image_detection import inference
from image_detection.utils import file_helper


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
        self.image_hub = CustomImageHub()
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.ckpt_path = os.path.join(self.dir_path, "checkpoint/best_ckpt.pt")
        # download model
        # file_helper.ModelDownload(self.ckpt_path)
        
        # initialize inference class
        self.inf = inference.Inference(self.ckpt_path)
        
    def start(self):
        # keep track of recognized ids
        self.recognized_ids = []
        print('[Image Server] Started image processing server')
        
        while True:
            try:
                print('[Image Server] Waiting for image from RPi')

                # receive RPi name and frame from the RPi and acknowledge the receipt
                _, frame = self.image_hub.recv_image()
                print('[Image Server] Connected and received frame at time: ' + str(datetime.now()))

                identifier = str(time.time()).split('.')[0]
                # form image file path for saving
                raw_image_name = "img_" + identifier + ".jpg"
                raw_image_path = os.path.join(self.dir_path, "images", raw_image_name)

                # check if images folder exists
                directory_images = os.path.join(self.dir_path, "images")
                if not os.path.exists(directory_images):
                    os.makedirs(directory_images)

                # save raw image
                cv2.imwrite(raw_image_path, frame)

                # run inference
                self.label, self.cord_thres = self.inf.run_inference(raw_image_path, self.recognized_ids) 

                # draw bounding box if image detected
                if self.label != "-1" and self.label != "41":
                    # add to recognized ids
                    self.recognized_ids.append(self.label)
                    print(f"Detect Image ID: {self.label}")
                    self.inf.draw_bounding(self.label, self.cord_thres, raw_image_path, self.dir_path)
                else:
                    if self.label == "41":
                        print("Detected Bullseye")
                    else:
                        print("No image is being detected")
                
                self.image_hub.send_reply(self.label)

            except KeyboardInterrupt as e:
                print("[Image Server] Ctrl-C")
                break
            

    def end(self):
        print('[Image Server] Stopping image processing server')
        self.image_hub.send_reply('Done')
        # send_reply disconnects the connection
        print('[Image Server] Sent reply and disconnected at time: ' + str(datetime.now()) + '\n')

# Standalone testing.
if __name__ == '__main__':
    print("[Image Server] Starting up Image Server")
    image_hub = ImageProcessingServer()
    image_hub.start()