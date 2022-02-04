# Image Detection

## Train Image Model

### 1) Collect training images 
- Run camera_helper.py, specify `mode` and `img_id`. Move obstacle to different positions for variations
- Transfer images from RPI to computer, then start labelling the images


### 2) Labelling images for training
- Clone ModifiedOpenLabelling:
`git clone https://github.com/ivangrov/ModifiedOpenLabelling.git`
- Place images in `ModifiedOpenLabelling/images` folder and remove the examples
- Remove example files in `ModifiedOpenLabelling/bbox_txt` folder
- In `ModifiedOpenLabelling/class_list.txt`, add a new class per line 
- Install requirements.txt
- Run `python run.py` to start labelling images
- Run `python train_test_split.py` to split dataset

### 3) Train yolov5 on custom dataset
Open train_custom.ipynb in google colab to train. Follow instructions in notebook to get a checkpoint from training.

#### Training files:
- Images
    - Unlabelled images: [here](https://drive.google.com/drive/folders/10ZCGqfw15J3IYnxq7tHaD-6XWdoFgX22?usp=sharing) 
    - Labelled training dataset: [here](https://drive.google.com/drive/folders/1iktnVXs0W6Uimvz1A6cjyU8tAnH_Zp-1?usp=sharing) 
- yaml file
    - `custom_dataset.yaml`: [here](https://drive.google.com/file/d/1TvoxBxlmI0rwjuhVkSPUm5tR6pg6J0u8/view?usp=sharing) 


## Inference
### Run inference codes
- Codes to run inference are under `inference.py`
- Uncomment model download line if there is a need to download model

#### Checkpoint files:
- Checkpoints: [here](https://drive.google.com/drive/folders/1ZHrY_ALSmzngmvtJ08LKtivsNKTM01Zu?usp=sharing) 

