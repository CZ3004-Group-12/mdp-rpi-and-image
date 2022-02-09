import torch
import cv2
import time

from image_detection.config.config import IMAGE_IDS

class Inference:
    '''
        Class to run inference
    '''
    def __init__(self, model_path):
        self.model_path = model_path
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=self.model_path)
        self.device = 'cpu'
        self.classes = self.model.names

    def run_inference(self, img_path):
        print("------ Starting detection ------")
        # Inference
        self.model.to(self.device)
        results = self.model(img_path)
        
        # get labels and coordinates
        labels, cord_thres = results.xyxyn[0][:, -1].numpy(), results.xyxyn[0][:, :-1].numpy()

        # if labels detected
        if len(labels) > 0:
            max_thres = 0
            # get max thres
            for idx, detected in enumerate(cord_thres):
                if detected[-1] > max_thres:
                    max_thres = detected[-1]
                    # get class
                    detected_img_id = self.classes[int(labels[idx])]
                    cords = detected

            # if threshold less than 0.75, then counted as not detected, else just leave it as it is
            if max_thres < 0.75:
                detected_img_id = "-1"
                cords = [] 
        # if no labels detected
        else:
            detected_img_id = "-1"
            cords = [] 
        
        # return results
        return detected_img_id, cords

    def draw_bounding(self, label, cord_thres, img_path):
        
        id_dict = IMAGE_IDS

        # read image
        img_taken = cv2.imread(img_path)

        # get x,y axes of bounding box
        x_shape, y_shape = img_taken.shape[1], img_taken.shape[0]
        x1, y1, x2, y2 = int(cord_thres[0]*x_shape), int(cord_thres[1]*y_shape), int(cord_thres[2]*x_shape), int(cord_thres[3]*y_shape)
        bgr = (128, 24, 33)

        # Draw bounding box
        cv2.rectangle(img_taken, (x1, y1), (x2, y2), bgr, 2)

        # get labels to display
        desc = id_dict[label]
        id_str =  "Image ID=" + label

        # draw bg for text 
        cv2.rectangle(img_taken, (x2+20, y1), (x2 + 250, y1 + 100), (255,255,255), -1)

        # draw text
        cv2.putText(img_taken, desc, (x2+40, y1+40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, bgr, 2)
        cv2.putText(img_taken, id_str, (x2+40, y1+80), cv2.FONT_HERSHEY_SIMPLEX, 0.9, bgr, 2)

        # get output path
        output_path = img_path.split(".")[0] + "_detected." + img_path.split(".")[1]
        # save image
        cv2.imwrite(output_path, img_taken)  


if __name__ == "__main__":
    # download model if needed
    # from utils.file_helper import ModelDownload
    # md = ModelDownload("best_ckpt.pt")

    # start inference
    start_time = time.time()
    
    inf = Inference("best_ckpt.pt")
    img_path = "test_images/11.jpg"
    label, cord_thres = inf.run_inference(img_path) 

    # draw bounding box
    # if label != "-1":
    #     inf.draw_bounding(label, cord_thres, img_path)

    end_time = time.time()
    
    print("Detected class: ", label, cord_thres)
    print("Total time taken: ", str(end_time-start_time))