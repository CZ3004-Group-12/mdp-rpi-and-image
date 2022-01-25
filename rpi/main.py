import os
import argparse
from util.config import IMAGE_PROCESSING_SERVER_URLS

parser = argparse.ArgumentParser(description="RPI Main Process")
parser.add_argument(
    '-i',
    '--image_recognition',
    default=None
)

def init():
    args = parser.parse_args()
    image_processing_server = args.image_recongition

    os.system("sudo hciconfig hci0 piscan")


if __name__ == "__main__":
    init()