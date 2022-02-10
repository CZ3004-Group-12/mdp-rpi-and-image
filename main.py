from rpi.etc import image_server
from image_detection.utils import display_images

# TODO: possibly add algo server
def start_all():
    image_hub = image_server.ImageProcessingServer()
    # TODO: to remove once everything connected properly
    image_hub.start()

if __name__ == "__main__":
    # start up server
    start_all()
    # once completed, open up window displaying results
    display_images.get_results()