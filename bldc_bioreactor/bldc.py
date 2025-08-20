from serial_port import SerialPort
from utils import read_json
import time

class BLDC:
    def __init__(self, serial_port: SerialPort):
        self.__serial_port = serial_port

    def get_status(self):
        return self.__serial_port.communicate(command = "status")

    #timeout in sec
    def set_timer(self, timeout: int):
        return  self.__serial_port.communicate(command = f"setTimer:{str(timeout)}")

    #velocity in rpm
    def set_velocity(self, velocity: float):
        return  self.__serial_port.communicate(command = f"setVelocity:{str(velocity)}")

    #acceleration in rpm^2
    def set_acceleration(self, acceleration: float):
        return  self.__serial_port.communicate(command = f"setAcceleration:{str(acceleration)}")

    def run_motor(self, doRun: bool):
        if doRun:
            value = "0"
        else:
            value = "1"
        return self.__serial_port.communicate(command = f"runMotor:"+value)

    def setup_done(self):
        self.__serial_port.communicate(command="setupDone:1")

    def basic_setup_routine(self):
        data = read_json()
        pin_string = ",".join(str(data[key]) for key in ["en1", "en2", "en3", "in1", "in2", "in3"])
        setup_pin_cmd = f"setupPin:{pin_string}"

        prescale_str = data["prescale"]
        prescale_cmd = f"setPrescale:{prescale_str}"

        self.__serial_port.communicate(command = setup_pin_cmd)
        time.sleep(1)
        self.__serial_port.communicate(command=prescale_cmd)
        time.sleep(1)
        self.__serial_port.communicate(command = "setupDone:1")