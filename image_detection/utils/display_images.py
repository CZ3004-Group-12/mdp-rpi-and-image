import os
import tkinter as tk 
import math
import numpy as np 
import cv2
from PIL import Image, ImageTk

def create_results(dir_path):
    width = 450
    height= 360
    
    directory_images_final = os.path.join(dir_path, "final")
    if not os.path.exists(directory_images_final):
        os.makedirs(directory_images_final)

    # get detected images path
    detect_path = f"{dir_path}/images_detected/"

    # Removes .DS_STORE by macos
    files = [f for f in os.listdir(detect_path) if not f.startswith('.')]

    # get total images in folder
    image_count = 0
    for file in files:
        image_count += 1

    each_row_count = math.ceil(image_count/2)

    # get first row first image
    first_file_name = files[0]
    vis_row_1 = cv2.imread(f"{detect_path}/{first_file_name}")
    vis_row_1 = cv2.resize(vis_row_1, (width, height))

    # get second row second image
    second_file_name = files[each_row_count]

    vis_row_2 = cv2.imread(f"{detect_path}/{second_file_name}")
    vis_row_2 = cv2.resize(vis_row_2, (width, height))

    # stitch other images in rows
    for idx, file in enumerate(files):
        if idx != 0:
            if idx < each_row_count:
                add_img = cv2.imread(f"{detect_path}/{file}")
                add_img = cv2.resize(add_img, (width, height))
                vis_row_1 = np.concatenate((vis_row_1, add_img), axis=1)
                cv2.imwrite(f"{dir_path}/final/out_row_1.jpg", vis_row_1)
                
            else:
                if idx != each_row_count:
                    add_img = cv2.imread(f"{detect_path}/{file}")
                    add_img = cv2.resize(add_img, (width, height))
                    vis_row_2 = np.concatenate((vis_row_2, add_img), axis=1)
                    cv2.imwrite(f"{dir_path}/final/out_row_2.jpg", vis_row_2)

    # if odd number, means need to pad bottom image
    if image_count != (each_row_count*2):
        btm_img = cv2.imread(f"{dir_path}/final/out_row_2.jpg")
        btm_img = cv2.copyMakeBorder(btm_img, 0, 0, 0, width, cv2.BORDER_CONSTANT, value=[255, 255, 255])
        cv2.imwrite(f"{dir_path}/final/out_row_2.jpg", btm_img)

    # get top and bottom image
    top_img = cv2.imread(f"{dir_path}/final/out_row_1.jpg")
    btm_img = cv2.imread(f"{dir_path}/final/out_row_2.jpg")
    # stich 2 rows together
    final_img = np.concatenate((top_img, btm_img), axis=0)
    cv2.imwrite(f"{dir_path}/final/final_out.jpg", final_img)

    
def get_results(dir_path):
    root = tk.Tk()
    
    # create stiched images
    create_results(dir_path)
    # open tkinter window with all images
    display_img = ImageTk.PhotoImage(Image.open(f"{dir_path}/final/final_out.jpg"))
    panel = tk.Label(root, image = display_img)
    panel.pack(side="bottom", fill="both", expand="yes")

    root.mainloop()

if __name__ == '__main__':
    dir_path = os.path.dirname(os.path.realpath(__file__))
    get_results(dir_path)