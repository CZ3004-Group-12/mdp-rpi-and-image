import numpy as np
import math 

from image_detection.config.config import DISTANCE_BOX_SIZE

class CorrectionHelper():
    '''
        Class to provide corrections based on image
        x_shape: size of the image horizontally
        y_shape: size of the image vertically
        x1, x2: coordinates of bounding box in x, based on image size
        y1, y2: coordinates of bounding box in y, based on image size
    '''
    def __init__(self, x_shape, y_shape, x1, x2, y1, y2):
        self.x_shape = x_shape
        self.y_shape = y_shape
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
    
    '''
        Calculate distance of obstacle from the robot,
        based on bounding box detected
        Returns distance
    '''
    # TODO: Change to get distance from ultrasonic sensor
    def calc_distance(self):
        height = self.y2 - self.y1 
        dist = 0    
    
        for h in DISTANCE_BOX_SIZE:
            if height > h:
                dist = DISTANCE_BOX_SIZE[h]
                break 

        return dist 

    '''
        Calculate position of robot(left/right of robot),
        based on whether detected bounding box is left or right
        Returns position of obstacle: LEFT | RIGHT | CENTRE
    '''
    def calc_position(self):
        x_half = int(self.x_shape/2)
        mid_x = self.x1 + ((self.x2-self.x1)/2)
        if mid_x < x_half:
            return "LEFT"
        elif mid_x > x_half:
            return "RIGHT"
        else: 
            return "CENTRE"     

    '''
        Calculate angle of bounding box, whether is is slanted to left or right
        Returns angle
    '''
    def calc_angle(self):
        offset_x = int ((self.x2 - self.x1)/10)
        offset_y = int ((self.y2 - self.y1)/10)

        interval_x = int((self.x2 - self.x1 - 2 * offset_x)/2)
        interval_y = int((self.y2 - self.y1 - 2 * offset_y)/2)
        
        points = np.zeros([9, 3])
        for i in range(3):
            for j in range(3):
                x = int(self.x1) + offset_x + interval_x*i
                y = int(self.y1) + offset_y + interval_y*i
                dist = self.calc_distance()
                # TODO: Find a way to get ppx/ppy - coordinate of principal point of image
                # TODO: Find a way to get fx/fy - Focal length of image plane
                # x_temp = dist*(x - intr.ppx)/intr.fx
                # y_temp = dist*(y - intr.ppy)/intr.fy
                x_temp = 0
                y_temp = 0
                z_temp = dist 
                points[j+i*3][0] = x_temp
                points[j+i*3][1] = y_temp
                points[j+i*3][2] = z_temp 

        params = self.find_plane(points)
        
        horizontal_angles = math.atan(params[2]/params[0])*180/math.pi
        if horizontal_angles < 0:
            horizontal_angles = horizontal_angles + 90
        else:
            horizontal_angles = horizontal_angles - 90

    def find_plane(self, points):
        # get center of pints 
        c = np.mean(points, axis=0)
        # Each point subtract centroid
        r0 = points - c 
        # SVD decomposition
        u, s, v = np.linalg.svd(r0)
        nv = v [-1, :]
        ds = np.dot(points, nv)
        param = np.r_[nv, -np.mean(ds)]
        return param 




