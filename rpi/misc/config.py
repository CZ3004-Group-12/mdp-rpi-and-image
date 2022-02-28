# Encoding / Decoding Format
FORMAT = "utf-8"

# STM
SERIAL_PORT = ['/dev/ttyUSB0', '/dev/ttyUSB1']
BAUD_RATE = 115200

# Bluetooth Settings / # Hua Wei Phone
# RFCOMM_CHANNEL = 12
ANDROID_SOCKET_BUFFER_SIZE = 1024
BLUETOOTH_ADDR = "34:12:F9:4B:2B:C5"
UUID = "87b585d1-84c3-486a-8f3d-77cf16f84f30"

# WiFi Settings
PORT = 5050
WIFI_IP = "192.168.12.12"
ALGO_SOCKET_BUFFER_SIZE = 1024

# Image Recongition Server
IMAGE_WIDTH = 640
IMAGE_HEIGHT = 480
IMAGE_FORMAT = 'bgr'
IMAGE_SEVER_ADDR = (WIFI_IP, PORT)
BASE_SERVER_PATH = "tcp://192.168.12."
IMAGE_SERVER_PORT = 5555
IMAGE_PROCESSING_SERVER_URLS = {
    "jacob" : f"{BASE_SERVER_PATH}29:{str(IMAGE_SERVER_PORT)}",
    "guanwei": f"{BASE_SERVER_PATH}25:{str(IMAGE_SERVER_PORT)}"
}

