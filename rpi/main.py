import os
import argparse
from misc.config import IMAGE_PROCESSING_SERVER_URLS
import imagezmq
from src.multi_processing import MultiProcessing
parser = argparse.ArgumentParser(description="RPI Main Process")
parser.add_argument(
    '-i',
    '--image_server',
    default=None
)

def init():
    args = parser.parse_args()
    member_name = args.image_server
    os.system("sudo hciconfig hci0 piscan")
    multi_process = None
    try:
        multi_process = MultiProcessing(
            IMAGE_PROCESSING_SERVER_URLS.get(member_name)
        )
        multi_process.start()
    except Exception:
        multi_process.end()

if __name__ == "__main__":
    init()