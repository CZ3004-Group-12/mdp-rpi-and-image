# Image recognition

## Train Image Model

### 1) Collect training images 
- Run camera_helper.py, specify `mode` and `img_id`. Move obstacle to different positions for variations
- Transfer images from RPI to computer ...


### 2) Labelling images for training
- Clone ModifiedOpenLabelling
`git clone https://github.com/ivangrov/ModifiedOpenLabelling.git`
- Place images in `ModifiedOpenLabelling/images` folder and remove the examples
- Remove example files in `ModifiedOpenLabelling/bbox_txt` folder
- In `ModifiedOpenLabelling/class_list.txt`, add a new class per line 
- Install requirements.txt
- Run `python run.py` to start labelling images

### 3) Train yolov5 on custom dataset
Open train_custom.ipynb in google colab to train. Follow instructions in notebook to get checkpoint from training.

#### Training files:
- Labeled training dataset: https://drive.google.com/drive/folders/1iktnVXs0W6Uimvz1A6cjyU8tAnH_Zp-1?usp=sharing 
- `custom_dataset.yaml`: https://drive.google.com/file/d/1TvoxBxlmI0rwjuhVkSPUm5tR6pg6J0u8/view?usp=sharing 

#### Inference file:
- `best_epoch_first_test.pt`: https://drive.google.com/file/d/1PjmJgPMwzpig0ll79lZFYwg388Mpbp3C/view?usp=sharing 