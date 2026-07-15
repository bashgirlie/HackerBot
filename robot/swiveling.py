from Raspi_MotorHAT.Raspi_PWM_Servo_Driver import PWM
import atexit
from time import sleep

class Swivel:
    def __init__(self, addr=0x6f, deflect_90_ms=0.6):
        """addr: i2c address of the PWM chip
        deflect_90_ms: set this to calibrate servo motor.
        It is deflection of 90 degrees in terms of a pulse length
        in milliseconds"""
        self._pwm = PWM(addr)
        pwm_freq = 100
        self._pwm.setPWMFreq(pwm_freq)
        servo_midpoint_ms = 1.5
        period_ms = 1000/pwm_freq
        #chip has 4096 steps in each period
        pulse_steps = 4096
        steps_per_ms = pulse_steps / period_ms
        #steps for a degree
        self.steps_per_degree = (deflect_90_ms * steps_per_ms) / 90
        #midpoint in steps
        self.servo_midpoint_steps = servo_midpoint_ms * steps_per_ms

    def stop_servo(self):
        # 0 in start is nothing, 4096 sets the OFF bit
        off_bit = 4096
        self._pwm.setPWM(0, 0, off_bit)
    
    def _convert_degrees_to_steps(self, position):
        return int(self.servo_midpoint_steps + (position* self.steps_per_degree))

    def set_servo_angle(self, angle):
        """position: The position in degrees from the center.
        -90 to 90."""
        # Validate
        if angle > 90 or angle < -90:
            raise ValueError("Angle outside of range!")
        #set position
        off_step = self._convert_degrees_to_steps(angle)
        self._pwm.setPWM(0, 0, off_step)
        sleep(0.25)




        
