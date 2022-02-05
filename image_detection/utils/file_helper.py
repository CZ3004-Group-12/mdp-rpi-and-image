import gdown
import os 

from config.config import MODEL_URL

class ModelDownload:
    '''
        Class to download model
    '''
    def __init__(self, model_path):
        self.model_url = MODEL_URL
        self.model_path = model_path
        # Download model
        gdown.download(self.model_url, self.model_path, quiet=False)


