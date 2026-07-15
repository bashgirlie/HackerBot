# super_sonic.py

from swiveling import Swivel
import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

GPIO_TRIGGER = 27
GPIO_ECHO = 17

GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)

class SuperSonic:
    ANGLE_RANGE = 180
    
    def __init__(self, timeout=0.1):
        self.servo = Swivel()
        self.timeout = timeout
        self.angle_distance = [0,0]
        self.current_angle = 0
        self.max_angle = self.ANGLE_RANGE/2
        self.min_angle = -self.ANGLE_RANGE/2
        self.scan_list = []
        self.trig = GPIO_TRIGGER
        self.echo = GPIO_ECHO

    def get_distance(self):
        GPIO.output(self.trig, False)
        time.sleep(0.01)
        GPIO.output(self.trig, True)
        time.sleep(0.00002)
        GPIO.output(self.trig, False)
        pulse_end = 0
        pulse_start = 0
        timeout_start = time.time()
        while GPIO.input(self.echo) == 0:
            pulse_start = time.time()
            if pulse_start - timeout_start > self.timeout:
                return 30
        while GPIO.input(self.echo) == 1:
            pulse_end = time.time()
            if pulse_end - timeout_start > self.timeout:
                return 32
        during = pulse_end - pulse_start
        inches = during * (6750/2)
        return inches
    
    def get_distance_at(self, angle):
        time.sleep(0)
        self.servo.set_servo_angle(angle)
        self.current_angle = angle
        time.sleep(0.01)
        distance = self.get_distance()
        self.angle_distance = [angle, distance]
        return distance
    
    def return_angle_distance(self):
        return self.angle_distance

