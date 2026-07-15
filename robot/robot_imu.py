from icm20948 import ICM20948

class RobotImu:
    def __init__(self):
        self._imu = ICM20948()

    def read_temp(self):
        return self._imu.read_temperature()

    def read_accelerometer(self):
        accel_x, accel_y, accel_z, _, _, _ = self._imu.read_accelerometer_gyro_data()
        return accel_x, accel_y, accel_z


def test():
    imu = RobotImu()
    while True:
        imu.read_accelerometer()
        speed = imu.read_accelerometer()
        print(speed)

#test()
