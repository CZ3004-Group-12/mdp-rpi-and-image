import time
import argparse

from picamera import PiCamera


camera = PiCamera()
camera.resolution = (640, 480)

'''
    Take photos for training
'''
def take_photo(image_id):
    # change rotation if camera on a different orientation
    camera.rotation = -180
    # To change image id and background type
    img_id = image_id
    background = "_first_bg"

    print("Count down")
    for j in range(5):
        time.sleep(1)
        print(5 - j)

    # to capture multiple angles of images
    for i in range(9):
        camera.capture("img" + "_" + str(img_id) + "_" + str(i) + background + ".jpg")
        print("Done for image " + str(img_id) + "_" + str(i))
        time.sleep(1)

        if i != 8:
            print("Next: " + str(i + 2))
            print("Count down")
            for j in range(7):
                time.sleep(1)
                print(7 - j)

        print("Done for image " + str(img_id))


if __name__ == "__main__":
    # argparser
    parser = argparse.ArgumentParser(description="Specify image IDs")
    parser.add_argument(
        "--img_id",
        help="Specify an image id that is more than 0",
        default=-1,
        type=int,
        required=True,
    )

    args = parser.parse_args()

    if args.img_id == -1:
        print("Please specify an image id that is more than 0")
    else:
        print("Starting camera to take photos")
        take_photo(args.img_id)
