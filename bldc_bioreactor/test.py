import serial
import time

class SerialPort:
    def __init__(self, port_name, baudrate=9600, timeout=2):
        self.__serial = serial.Serial(port_name, baudrate=baudrate, timeout=timeout)
        time.sleep(2)

    def communicate(self, cmd):
        try:
            self.__serial.flushInput()
            self.__serial.flushOutput()
            print(f"Sending: {cmd}")

            if not cmd.endswith("\n"):
                cmd += "\n"

            self.__serial.write(cmd.encode('utf-8'))

            start_time = time.time()
            response = ""
            while True:
                if self.__serial.in_waiting > 0:
                    line = self.__serial.readline().decode('utf-8').strip()
                    response += line
                    print(f"Received line: {line}")
                    break
                if time.time() - start_time > 2:
                    raise Exception("No response received.")

            print("Response received:", response)
            return response

        except Exception as e:
            print("Errrror:", e)
            raise Exception("Could not send command") from e


ser = SerialPort("COM10")
time.sleep(2)
ser.communicate("setupPin:2,3,4,5,6,7")