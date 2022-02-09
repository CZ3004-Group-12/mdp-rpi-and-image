from rpi.etc import image_server

# TODO: possibly add algo server
def start_all():
    image_hub = image_server.ImageProcessingServer()
    # TODO: to remove once everything connected properly
    image_hub.start()

if __name__ == "__main__":
    start_all()