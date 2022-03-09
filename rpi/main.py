import os
import argparse
from src.multi_processing import MultiProcessing
from misc.config import IMAGE_PROCESSING_SERVER_URLS

parser = argparse.ArgumentParser(description="Main Process For RPI")

parser.add_argument(
    '--img_server',
    type=str,
    default=None,
    required=False,
    choices=IMAGE_PROCESSING_SERVER_URLS.keys())

parser.add_argument( '--stm', type=bool, default=True, required=False,)
parser.add_argument( '--algo', type=bool, default=True, required=False,)
parser.add_argument( '--android', type=bool, default=True, required=False,)
parser.add_argument( '--env', type=bool, default="outdoor", required=False,)
parser.add_argument( '--us', type=bool, default=False, required=False,)

def init():
    multi_process = None
    args = parser.parse_args()
    os.system("sudo hciconfig hci0 piscan")
    try:
        server_host = IMAGE_PROCESSING_SERVER_URLS[args.img_server] if args.img_server in IMAGE_PROCESSING_SERVER_URLS else None
        multi_process = MultiProcessing(
            image_processing_server=server_host, 
            android_on=args.android, 
            stm_on=args.stm,
            algo_on=args.algo, 
            env=args.env,
            ultrasonic_on=args.us,
            )
        multi_process.start()

    except Exception as error:
        print(f"[Main] Error have occurred: {error}")
        if multi_process is not None:
            multi_process.end()

if __name__ == "__main__":
    init()