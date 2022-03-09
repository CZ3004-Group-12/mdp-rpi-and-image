
import os
import time
import cv2
from imagezmq import ImageHub
from datetime import datetime

from rpi.misc.config import *
from image_detection import inference
from image_detection.utils import file_helper, display_images, correction_helper


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
        # download model if not downloaded
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
                rpi_reply, frame = self.image_hub.recv_image()
                print('[Image Server] Connected and received frame at time: ' + str(datetime.now()))

                print("Recognized IDS:", self.recognized_ids)
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
                self.label, self.cord_thres, x_shape, y_shape, bbox = self.inf.run_inference(raw_image_path, self.recognized_ids) 

                # draw bounding box if image detected
                if self.label != "-1" and self.label != "41":
                    if rpi_reply != "calibrate":
                        # add to recognized ids
                        self.recognized_ids.append(self.label)
                        print(f"Detect Image ID: {self.label}")
                        self.inf.draw_bounding(self.label, self.cord_thres, raw_image_path, self.dir_path)

                        # check distance
                        ch = correction_helper.CorrectionHelper(x_shape, y_shape, bbox[0], bbox[2], bbox[1], bbox[3])
                        dist = ch.calc_dist()
                        post = ch.calc_position()
                        reply = f"{self.label}/{dist}"
                    else:
                        # check position after adjusting distance
                        ch = correction_helper.CorrectionHelper(x_shape, y_shape, bbox[0], bbox[2], bbox[1], bbox[3])
                        post = ch.calc_position()
                        print(f"Coord Difference: {post}")
                        reply = post 
                else:
                    if self.label == "41":
                        print("Detected Bullseye")
                    else:
                        print("No image is being detected")
                    reply = "-1"
                
                self.image_hub.send_reply(reply)

                # if last obstacle detected, reset recognized list and display images
                if (rpi_reply == 1 and self.label != "-1") or (rpi_reply == 0):
                    self.recognized_ids = []
                    display_images.get_results(self.dir_path)

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
    dir_path = os.path.dirname(os.path.realpath(__file__))
    display_images.get_results(dir_path)

    #print("[Image Server] Starting up Image Server")
    #image_hub = ImageProcessingServer()
    #image_hub.start()