import time
import RPi.GPIO as GPIO
 
class UltraSonic(object):
    def __init__(self) -> None:
        #GPIO Mode (BOARD / BCM)
        GPIO.setmode(GPIO.BCM)
 
        #set GPIO Pins
        self.GPIO_ECHO = 24
        self.GPIO_TRIGGER = 23
 
        #set GPIO direction (IN / OUT)
        GPIO.setup(self.GPIO_ECHO, GPIO.IN)
        GPIO.setup(self.GPIO_TRIGGER, GPIO.OUT)

    def distance(self) -> int:

        GPIO.output(self.GPIO_TRIGGER, True)
        # set Trigger after 0.01ms to LOW
        time.sleep(0.00001)
        GPIO.output(self.GPIO_TRIGGER, False)
        
        StartTime = StopTime = time.time()
        
        # save StartTime
        while GPIO.input(self.GPIO_ECHO) == 0:
            StartTime = time.time()
    
        # save time of arrival
        while GPIO.input(self.GPIO_ECHO) == 1:
            StopTime = time.time()
    
        # time difference between start and arrival
        TimeElapsed = StopTime - StartTime
        # multiply with the sonic speed (34300 cm/s)
        # and divide by 2, because there and back
        distance = (TimeElapsed * 34300) / 2
    
        return int(distance)
 
if __name__ == '__main__':
    ultrasonic = UltraSonic()
    try:
        while True:
            dist = ultrasonic.distance()
            print ("Measured Distance = %d cm" % dist)
            time.sleep(1)
 
        # Reset by pressing CTRL + C
    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup()