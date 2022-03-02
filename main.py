from rpi.etc import image_server
from image_detection.utils import correction_helper

if __name__ == "__main__":
    # start up server
    image_hub = image_server.ImageProcessingServer()
    # # once completed, open up window displaying results
    image_hub.start()



