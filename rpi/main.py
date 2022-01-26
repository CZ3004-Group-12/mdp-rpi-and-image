import os
import argparse
from misc.config import IMAGE_PROCESSING_SERVER_URLS
from src.multi_processing import MultiProcessing

parser = argparse.ArgumentParser(description="RPI Main Process")
parser.add_argument(
    '--image_server_host',
    type=str,
    required=False,
    default=None,
    choices =IMAGE_PROCESSING_SERVER_URLS.keys(),
)

def init():
    args = parser.parse_args()
    server_host = args.image_server_host
    os.system("sudo hciconfig hci0 piscan")
    multi_process = None
    try:
        print(server_host)
        if server_host not in IMAGE_PROCESSING_SERVER_URLS:
            print("[Main] Image Server Host doesn't exist.")
            return
        multi_process = MultiProcessing(IMAGE_PROCESSING_SERVER_URLS[server_host])
        multi_process.start()
    except Exception as error:
        print(error)
        if multi_process is not None:
            multi_process.end()

if __name__ == "__main__":
    init()