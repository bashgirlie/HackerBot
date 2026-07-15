#test_motors.py

from Raspi_MotorHAT import Raspi_MotorHAT
#from gpiozero import DistanceSensor
from swiveling import Swivel
from super_sonic import SuperSonic
from robot_imu import RobotImu
import threading
import time, atexit
from randint_test import randomBinary

class RPibot(object):
    def __init__(self, motorhat_addr=0x6f):
        #setup the motorhat with the passed in address
        self._mh = Raspi_MotorHAT(addr=motorhat_addr)

        #get local variable for each motor upto 4
        self.fL = self._mh.getMotor(1)
        self.fR = self._mh.getMotor(2)
        self.bL = self._mh.getMotor(3)
        self.bR = self._mh.getMotor(4)

        #setup the distance sensors
        #self.left_distance_sensor = DistanceSensor(echo=17, trigger=27, queue_len=2)
        #self.right_distance_sensor = DistanceSensor(echo=5, trigger=6, queue_len=2)

        # set up servo
        self.servo = Swivel(addr=motorhat_addr)
        #set up ultrasonic sensor
        self.supersonic = SuperSonic()

        #set up IMU
        self.imu = RobotImu()

        #make sure motors stop when code exits
        
        atexit.register(self.stop_all)

    #convert speed & mode
    def convert_speed(self, speed):
        #choose the running mode
        mode = Raspi_MotorHAT.RELEASE
        if speed > 0:
            mode = Raspi_MotorHAT.FORWARD
        elif speed < 0:
            mode = Raspi_MotorHAT.BACKWARD
        
        #Scale the speed 
        output_speed = (abs(speed) * 255) // 100
        return mode, int(output_speed)
    
    #use speed conversion to change motor movements
    def set_front_left(self, speed):
        mode, output_speed = self.convert_speed(speed)
        self.fL.setSpeed(output_speed)
        self.fL.run(mode)
    def set_back_left(self, speed):
        mode, output_speed = self.convert_speed(speed)
        self.bL.setSpeed(output_speed)
        self.bL.run(mode)
    def set_front_right(self, speed):
        mode, output_speed = self.convert_speed(speed)
        self.fR.setSpeed(output_speed)
        self.fR.run(mode)
    def set_back_right(self, speed):
        mode, output_speed = self.convert_speed(speed)
        self.bR.setSpeed(output_speed)
        self.bR.run(mode)

    #define a moveset
    def go_straight(self, speed):
        """set all wheels going forward with
        same speed"""
        self.set_front_left(speed)
        self.set_front_right(speed)
        self.set_back_left(speed)
        self.set_back_right(speed)
    
    def go_backwards(self, speed):
        """set all wheels going backwards with
        same speed"""
        speed = -speed
        self.set_front_left(speed)
        self.set_front_right(speed)
        self.set_back_left(speed)
        self.set_back_right(speed)

    def turn_left(self, speed):
        """'normal' leftwards turn"""
        speed = speed*1.5
        self.set_front_left(speed)
        self.set_front_right(-speed)
        self.set_back_left(speed)
        self.set_back_right(-speed)
    
    def turn_right(self, speed):
        """'normal' rightwards turn"""
        speed = speed*1.5
        self.set_front_left(-speed)
        self.set_front_right(speed)
        self.set_back_left(-speed)
        self.set_back_right(speed)

    def rand_turn_around(self, speed):
        n = randomBinary()
        self.go_backwards(speed)
        time.sleep(0.5)
        if n == 0:
            self.turn_right(speed)
            time.sleep(1.5)
        elif n == 1:
            self.turn_left(speed)
            time.sleep(1.5)
        
    # define different movesets

    #stop motors
    def stop_motors(self):
        """stops all the wheels"""
        self.fL.run(Raspi_MotorHAT.RELEASE)
        self.fR.run(Raspi_MotorHAT.RELEASE)
        self.bL.run(Raspi_MotorHAT.RELEASE)
        self.bR.run(Raspi_MotorHAT.RELEASE)
    
    def stop_all(self):
        self.stop_motors()
        self.servo.stop_servo()
        
    
    def set_pan(self, angle):
        """Robot3 uses Swivel class instead of Servo class.
        This allows for angles to determine position of the servo"""
        self.servo.set_servo_angle(angle)

    '''def display_distance(self):
        print('Distance: {s}'.format(s=self.distance_sensor.distance*self.dist_off))
'''
    def return_distance(self):
        return self.supersonic.get_distance()
    
    def return_distance_at(self, angle):
        return self.supersonic.get_distance_at(angle)
    
    def get_dist_angle_list(self):
        '''Return the [angle, distance] list'''
        self.supersonic.return_angle_distance()
    
    def get_speed(self):
        '''Uses the RobotImu class to read the accelerometer on the 10 DOF IMU (d)
        and returns only the x value (forward speed)'''
        measured_speed = self.imu.read_accelerometer()
        return measured_speed[0]

    def check_stopped(self):
        #This will count how long the robot has been stuck
        current_speed = self.get_speed()
        if (current_speed == 0 or current_speed <= 0.01):
            self.stuck_since = time.time()


