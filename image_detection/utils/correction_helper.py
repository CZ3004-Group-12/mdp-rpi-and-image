from matplotlib.pyplot import grid
import numpy as np
import math 

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
        # self.distance = distance 
    
    '''
        Calculate distance of obstacle from the robot,
        based on bounding box detected
        Returns distance
    '''
    def calc_dist(self): 
        img_height = 610
        # f_x = 786.94295638 
        # f_y = 790.81875267 
        # f = 3.04 
        # mid_y = f_y / f 
        
        height = self.y2-self.y1

        # dist_from_camera = img_height * f / height/mid_y
        f = 90
        dist_from_camera = f * img_height / height
        # to cm
        dist_from_camera = dist_from_camera/10
        print("dist cam:", dist_from_camera)
        
        # dist_from_camera = dist_from_camera * 1000
        camera_to_front = 23 
        dist_from_front_of_robot = dist_from_camera - camera_to_front
            
        grid_dist = dist_from_front_of_robot - 23.5

        if dist_from_front_of_robot > 23.5:
            grid_dist = grid_dist
        else:
            grid_dist = -grid_dist

        print(dist_from_camera, dist_from_front_of_robot)
        return grid_dist

    '''
        Calculate position of robot(left/right of robot),
        based on whether detected bounding box is left or right
        Assuming robot moves to a distance of 23.5cm away from the front of robot
        Returns position of obstacle: LEFT | RIGHT | CENTRE
    '''
    def calc_position(self):
        x_half = int(self.x_shape/2)
        mid_x = self.x1 + ((self.x2-self.x1)/2)

        pixels_to_mid = abs(x_half - mid_x)
        print("PIXEL TO MID: ", pixels_to_mid)

        # to left of robot
        if mid_x < x_half:
            # 25cm
            if pixels_to_mid > 400:
                return "-2"
            # 20cm
            elif pixels_to_mid > 300:
                return "-2"
            # 15cm
            elif pixels_to_mid > 200:
                return "-1"
            # 10cm
            elif pixels_to_mid > 100:
                return "-1"
            # 5cm
            elif pixels_to_mid > 50:
                return "-1"
            # no cm
            else: 
                return "0" 
        # to right of robot    
        else:
            # 25cm
            if pixels_to_mid > 400:
                return "2"
            # 20cm
            elif pixels_to_mid > 300:
                return "2"
            # 15cm
            elif pixels_to_mid > 200:
                return "1"
            # 10cm
            elif pixels_to_mid > 100:
                return "1"
            # 5cm
            elif pixels_to_mid > 50:
                return "1"
            # no cm
            else: 
                return "0" 
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
                # dist = self.calc_distance()
                dist = self.distance
                # TODO: Find a way to get ppx/ppy - coordinate of principal point of image
                # TODO: Find a way to get fx/fy - Focal length of image plane
                fx = 786.94295638
                fy = 790.81875267
                ppx = 518.75519123
                ppy = 393.20689252
                x_temp = dist*(x - ppx)/fx
                y_temp = dist*(y - ppy)/fy
                # x_temp = 0
                # y_temp = 0
                z_temp = self.distance 
                points[j+i*3][0] = x_temp
                points[j+i*3][1] = y_temp
                points[j+i*3][2] = z_temp 

        params = self.find_plane(points)
        # print(params)
        
        horizontal_angles = math.atan(params[2]/params[0])*180/math.pi
        if horizontal_angles < 0:
            horizontal_angles = horizontal_angles + 90
        else:
            horizontal_angles = horizontal_angles - 90

        print(horizontal_angles)

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
        print(param)
        return param 

if __name__ == '__main__':
    x_shape, y_shape, x1, x2, y1, y2, distance = 1024, 768, 230, 389, 458, 513, 50*10
    x1 = 535
    x2 = 618
    y1 = 498
    y2 = 575
    ch = CorrectionHelper(x_shape, y_shape, x1, x2, y1, y2)
    # ch.calc_angle()

    # print(ch.calc_position())
    print(ch.calc_dist())
