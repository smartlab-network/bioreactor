from serial import Serial, SerialTimeoutException
from threading import Lock
from utils import lock_threading_lock
import time

class SerialPort:
    def __init__(self, port: str, timeout: float = 10.0, baudrate: int = 9600):
        self.__serial = Serial(port, baudrate=baudrate,  timeout=timeout, write_timeout=timeout)
        time.sleep(2)
        self.__connected = True
        self.open_serial()
        self.__port = port
        self.__lock = Lock()
        self.__timeout = timeout

    def open_serial(self):
        if not self.__connected:
            self.__serial.open()
            time.sleep(2)

    def close_serial(self):
        if self.__connected:
            self.__serial.close()
            self.__connected = False

    def get_port(self):
        return self.__port

    def communicate(self, command: str) -> str:
        with lock_threading_lock(self.__lock, timeout=self.__timeout):
            try:
                # Flush input/output buffer (vorsichtig)
                self.__serial.reset_input_buffer()
                self.__serial.reset_output_buffer()
                time.sleep(0.1)

                if not isinstance(command, str):
                    raise ValueError("Command must be a string")

                # Send command with CR or CRLF if Arduino expects \r or \r\n
                full_command = command.strip() + "\r\n"
                self.__serial.write(full_command.encode('utf-8'))
                print(f">>> Sent: {full_command.strip()}")

                # Wait and read line-by-line until response or timeout
                start_time = time.time()
                response = b''

                while time.time() - start_time < self.__timeout:
                    if self.__serial.in_waiting > 0:
                        response = self.__serial.readline()
                        break
                    time.sleep(0.05)  # avoid tight loop

                if not response:
                    print("  No response received within timeout.")
                    raise TimeoutError("No response received from serial device.")

                decoded = response.decode('utf-8', errors='replace').strip()
                print(f"<<< Received: {decoded}")
                return decoded

            except SerialTimeoutException as e:
                print(f" Serial write timeout: {e}")
                raise Exception("Serial write timeout")

            except Exception as e:
                print(f" Serial communication error: {e}")
                raise Exception(f"Communication failed: {e}")