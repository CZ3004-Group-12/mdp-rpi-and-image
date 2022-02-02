import os
import argparse
from src.multi_processing import MultiProcessing
from misc.config import IMAGE_PROCESSING_SERVER_URLS

parser = argparse.ArgumentParser(description="Main Process For RPI")

parser.add_argument(
    type=str,
    default=None,
    required=False,
    name_or_flags='--img_server',
    choices =IMAGE_PROCESSING_SERVER_URLS.keys())

def init():
    multi_process = None
    args = parser.parse_args()
    server_host = args.img_server
    os.system("sudo hciconfig hci0 piscan")
    
    try:
        if server_host not in IMAGE_PROCESSING_SERVER_URLS:
            print("[Main] Running without Image Server Host.")
            multi_process = MultiProcessing()            
        else:
            print(f"[Main] Running with Image Server Host @ {server_host}")
            multi_process = MultiProcessing(IMAGE_PROCESSING_SERVER_URLS[server_host])
        multi_process.start()

    except Exception as error:
        print(f"[Main] Error have occurred: {error}")
        if multi_process is not None:
            multi_process.end()

if __name__ == "__main__":
    init()