import time
import socket
import imagezmq
from imutils.video import VideoStream

sender = imagezmq.ImageSender(connect_to='tcp://192.168.12.25:5555')

rpi_name = socket.gethostname() # send RPi hostname with each image
picam = VideoStream(usePiCamera=True).start()
time.sleep(2.0)  # allow camera sensor to warm up
while True:  # send images as stream until Ctrl-C
    image = picam.read()
    sender.send_image(rpi_name, image)