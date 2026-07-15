from Raspi_MotorHAT import Raspi_MotorHAT
from gpiozero import Robot
from swiveling import Swivel
from super_sonic import SuperSonic
from robot_imu import RobotImu
from robot import RPibot
import asyncio
import time


"""
Run on RaspberryPi bot with AP mode enabled on the Pi. Will use async for the different components of controlling the movements and waiting for commands,
Will use multithreading to put Pentesting processes on a different thread.
"""

last_heartbeat = None


class RobotState:
    def __init__(self):
        # Microsecond timestamp of the last received packet
        self.last_heartbeat = 0.0
        #state of wheel speeds

class RobotUDPProtocol(asyncio.DatagramProtocol):
    def __init__(self, state: RobotState):
        # Pass the shared whiteboard in so this class can write to it
        self.state = state

    def connection_made(self, transport):
        """Called automatically when the UDP socket opens successfully."""
        self.transport = transport
        print("[Network] Listening for RC commands on port 5005...")

    def datagram_received(self, data: bytes, addr):
        """Called automatically every single time a UDP packet arrives."""
        # 1. Decode the raw bytes from your laptop (e.g., b'FORWARD' or b'X,Y')
        command = data.decode().strip()
        
        # 2. Update the heartbeat timestamp immediately
        import time
        self.state.last_heartbeat = time.time()
        
        # 3. Parse the command and calculate the steering math
        # 4. Write the results directly to your whiteboard
        # self.state.left_speed = calculated_left
        # self.state.right_speed = calculated_righ


class ButterbotController:
    def __init__(self, state: RobotState):
        self.state = state
        self.stopping_distance = 10 
    
