from tracemalloc import start
import torch
import gdown
import time

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
        # save image
        results.save()
        # get class
        detected_img_id = self.classes[int(labels[0])]
        return detected_img_id

class ModelDownload:
    '''
        Class to download model
    '''
    def __init__(self, model_url, model_path):
        self.model_url = model_url
        self.model_path = model_path
        # Download model
        gdown.download(self.model_url, self.model_path, quiet=False)
        

if __name__ == "__main__":
    # download model if needed
    # md = ModelDownload("https://drive.google.com/uc?id=1EIWIDC2ntZ3D9DE9vWOip7c-6T_0YrT-", "best_ckpt.pt")

    # start inference
    start_time = time.time()
    inf = Inference("best_ckpt.pt")
    result = inf.run_inference("test_images/17.jpg") 
    end_time = time.time()
    
    print("Detected class: ", result)
    print("Total time taken: ", str(end_time-start_time))