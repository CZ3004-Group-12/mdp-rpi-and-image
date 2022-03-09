import os
import torch
import cv2
import time

# from image_detection.config.config import IMAGE_IDS
from .config.config import IMAGE_IDS

class Inference:
    '''
        Class to run inference
    '''
    def __init__(self, model_path):
        self.model_path = model_path
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=self.model_path)
        self.device = 'cpu'
        self.classes = self.model.names

    def run_inference(self, img_path, recognized_ids):
        print("------ Starting detection ------")
        # default values
        detected_img_id = "-1"
        cords = []
        thres = 0
        bbox = []

        # Inference
        self.model.to(self.device)
        results = self.model(img_path)
        
        # get labels and coordinates
        labels, cord_thres = results.xyxyn[0][:, -1].numpy(), results.xyxyn[0][:, :-1].numpy()
        
        # read image to get size of image
        img_taken = cv2.imread(img_path)
        x_shape, y_shape = img_taken.shape[1], img_taken.shape[0]

        # if labels detected
        if len(labels) > 0:
            max_area = 0

            # get bigger area
            for idx, detected in enumerate(cord_thres):
                # get coords 
                x1, y1, x2, y2 = int(detected[0]*x_shape), int(detected[1]*y_shape), int(detected[2]*x_shape), int(detected[3]*y_shape)
                bbox = [x1, y1, x2, y2]
                # get area
                x_len = abs(x2-x1)
                y_len = abs(y2-y1)
                area = x_len*y_len
                # get label
                curr_id = self.classes[int(labels[idx])]
                
                # if bigger than current, then reassign
                if (area > max_area) and (curr_id not in recognized_ids) and (curr_id != "41"):
                    thres = detected[-1]
                    # only store if threshold bigger than 0.75
                    if thres >= 0.75:
                        max_area = area
                        # get class
                        detected_img_id = curr_id
                        cords = detected
        # if no labels detected
        else:
            detected_img_id = "-1"
            cords = [] 
        
        # return results
        return detected_img_id, cords, x_shape, y_shape, bbox

    def draw_bounding(self, label, cord_thres, img_path, dir_path):
        id_dict = IMAGE_IDS

        # read image
        img_taken = cv2.imread(img_path)

        # get x,y axes of bounding box
        x_shape, y_shape = img_taken.shape[1], img_taken.shape[0]

        print("X_SHAPE:", x_shape)
        print("Y_SHAPE:", y_shape)

        # get halfway point of image
        x_half = int(x_shape/2)

        x1, y1, x2, y2 = int(cord_thres[0]*x_shape), int(cord_thres[1]*y_shape), int(cord_thres[2]*x_shape), int(cord_thres[3]*y_shape)
        bgr = (128, 24, 33)

        # Draw bounding box
        cv2.rectangle(img_taken, (x1, y1), (x2, y2), bgr, 2)

        # get labels to display
        desc = id_dict[label]
        id_str =  "Image ID=" + label

        # if bounding box to left of image, draw labels on right
        if x1 < x_half:
            # draw bg for text 
            cv2.rectangle(img_taken, (x2+20, y1), (x2+250, y1+100), (255,255,255), -1)
            # draw text
            cv2.putText(img_taken, desc, (x2+40, y1+40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, bgr, 2)
            cv2.putText(img_taken, id_str, (x2+40, y1+80), cv2.FONT_HERSHEY_SIMPLEX, 0.9, bgr, 2)
        # if bounding box to right of image, draw labels on left
        elif x1 >= x_half:
            # draw bg for text 
            cv2.rectangle(img_taken, (x1-20, y1), (x1-250, y1+100), (255,255,255), -1)
            # size of background for test
            bg_length = 250-20 
            # draw text
            cv2.putText(img_taken, desc, (x1-bg_length, y1+40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, bgr, 2)
            cv2.putText(img_taken, id_str, (x1-bg_length, y1+80), cv2.FONT_HERSHEY_SIMPLEX, 0.9, bgr, 2)

        # create output folder if not exists
        directory_detected = os.path.join(dir_path, "images_detected")
        if not os.path.exists(directory_detected):
            os.makedirs(directory_detected)

        # get output path
        file_name = label + ".jpg"
        output_path = os.path.join(directory_detected, file_name)
        # save image
        cv2.imwrite(output_path, img_taken)  


if __name__ == "__main__":
    # download model if needed
    # from utils.file_helper import ModelDownload
    # md = ModelDownload("best_ckpt.pt")

    # start inference
    start_time = time.time()
    
    inf = Inference("best_ckpt.pt")
    img_path = "test_images/img_76_0_first_bg.jpg"
    label, cord_thres = inf.run_inference(img_path, []) 

    # read image
    img_taken = cv2.imread(img_path)

    # get x,y axes of bounding box
    x_shape, y_shape = img_taken.shape[1], img_taken.shape[0]

    print("X_SHAPE:", x_shape)
    print("Y_SHAPE:", y_shape)

    x1, y1, x2, y2 = int(cord_thres[0]*x_shape), int(cord_thres[1]*y_shape), int(cord_thres[2]*x_shape), int(cord_thres[3]*y_shape)
    print(f"X1: {x1},  X2: {x2}")
    print(f"Y1: {y1}, Y2: {y2}")

    # draw bounding box
    # if label != "-1":
    #     inf.draw_bounding(label, cord_thres, img_path)

    end_time = time.time()
    
    print("Detected class: ", label, cord_thres)
    print("Total time taken: ", str(end_time-start_time))