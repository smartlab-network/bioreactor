import time
import ttkbootstrap as ttk
import threading

from utils import read_json, write_json, message_box_error
from serial import SerialException
from tkinter import StringVar
from serial_port import SerialPort
from datetime import datetime
from bldc import BLDC

class GUI:
    STANDARD_FONT = ('Helvetica', 14)
    MAX_COUNTER = 65535
    F_CPU = 16000000
    DEGREES_PER_PHASE = 10/360

    def __init__(self):
        self.__gui = ttk.Window(themename="darkly")
        self.__gui.title("BLDC Controller")
        self.__gui.geometry("1600x920")
        
        self.__serial_port = None
        self.bldc = None
        self.toplevel_settings = Setup(main = self)
        data = read_json()
        self.prescale: int = data['prescale']
        try:
            self.__serial_port = SerialPort(data["com_port"])
            self.bldc = BLDC(self.__serial_port)
            self.bldc.basic_setup_routine()
            self.toplevel_settings.withdraw()

        except SerialException as e:
            self.__gui.withdraw()
            if "FileNotFoundError" in str(e):
                message_box_error(error = "not found")

            elif "PermissionError" in str(e):
                message_box_error(error = "no permission")

            self.toplevel_settings.show()

        except Exception:
            self.__gui.withdraw()
            message_box_error(error = "unexpected error")
            self.toplevel_settings.show()
            self.gui_state = 'disabled'


        self.runnig: bool = False
        self.min_timeout: float
        """
        Defines the possible velocity interval
        """
        self.max_velocity_float: float = 300 #just saefty value, more is possbile
        self.min_velocity_float: float = self.calculate_min_velocity()#varies by the prescale

        self.curr_velocity_float: float = 0
        self.curr_velocity_str = StringVar()
        self.curr_velocity_str.set(f"{self.curr_velocity_float:.2f}")

        self.max_acceleration: float = 400 #just saefty value
        self.curr_acceleration_float: float = 0.0
        self.curr_acceleration_str = StringVar()
        self.curr_acceleration_str.set(f"{self.curr_acceleration_float:.2f}")

        self.timer: float =  0
        self.timer_str = StringVar()
        self.timer_str.set("0.00")
        self.check_timer_background = self.__gui.after(10000, self.check_timer)
        self.doTimer: bool = False

        self.frame_timeout = ttk.Frame(self.__gui)
        self.frame_velocity = ttk.Frame(self.__gui)

        style = ttk.Style()
        style.configure("info.Horizontal.TScale", troughcolor="#e0f3ff", sliderthickness=40)
        self.label_slider =             ttk.Label(self.__gui, text = "Maximum velocity: 0 rpm", font =("Helvetica", 12), anchor = 'center', width=60)

        self.slider =                   ttk.Scale(self.__gui, from_=0, to = 1, orient = "horizontal", command=self.callback_slider, style="info.Horizontal.TScale")

        self.label_set_velocity =       ttk.Label(self.__gui, text="Velocity rpm:", font = GUI.STANDARD_FONT, anchor='e')
        self.entry_set_velocity =       ttk.Entry(self.__gui, textvariable=self.curr_velocity_str, font =GUI.STANDARD_FONT, justify='center')

        self.label_set_acceleration =   ttk.Label(self.__gui, text = "Acceleration rpm^2:", font=GUI.STANDARD_FONT, anchor='e')
        self.entry_set_acceleration =   ttk.Entry(self.__gui, textvariable=self.curr_acceleration_str, font=GUI.STANDARD_FONT, justify='center')

        self.label_timeout =            ttk.Label(self.__gui, text = "Timeout min:", font=GUI.STANDARD_FONT, anchor='e')
        self.entry_timeout =            ttk.Entry(self.__gui, textvariable = self.timer_str, font = GUI.STANDARD_FONT, justify ="center")

        now = datetime.now()
        hour = now.strftime("%H")
        minute =now.strftime("%M")
        self.timeout_hour: int = int(hour)
        self.timeout_minute: int = int(minute)

        self.timeout_hour_str = StringVar()
        self.timeout_hour_str.set(f"{self.timeout_hour:02}")
        self.timeout_minute_str = StringVar()
        self.timeout_minute_str.set(f"{self.timeout_minute:02}")

        self.entry_hour =               ttk.Entry(self.__gui, textvariable=self.timeout_hour_str,font=GUI.STANDARD_FONT, justify='center', state = "disabled", width=30)
        self.entry_minute =             ttk.Entry(self.__gui, textvariable=self.timeout_minute_str,font=GUI.STANDARD_FONT, justify='center', state = "disabled", width=30)

        self.button_hour_up =           ttk.Button(self.__gui, text="˄", command = lambda: self.callback_hour(True), width = 10)
        self.button_hour_down =         ttk.Button(self.__gui, text="˅", command = lambda: self.callback_hour(False), width = 10)
        self.button_minute_up =         ttk.Button(self.__gui, text="˄", command = lambda: self.callback_minute(True), width = 10)
        self.button_minute_down =       ttk.Button(self.__gui, text="˅", command = lambda: self.callback_minute(False), width = 10)

        self.label_time_dott =          ttk.Label(self.__gui, text = " :", font = ("Helvetica", 20), width=5)

        self.button_run =               ttk.Button(self.__gui, text = "Run", command = self.callback_run, bootstyle = 'success', width = 10)

        self.button_timer_on =          ttk.Button(self.__gui, text = "Timer: Off", command = self.callback_timer_on, bootstyle = 'danger')
        self.button_save_timer =        ttk.Button(self.__gui, text = "Save timer", command = self.callback_save_button)


        self.button_settings = ttk.Button(text = "Settings", command = self.callback_settings)
        self.button_settings.grid(row = 0, column=9, sticky = 'nsew')
        

        """
        Gui widget arrangement is set by using Tkinter grid 
        """
        self.set_grid_settings()
        self.place_set_velocity()
        self.place_set_acceleration()
        self.place_timeout()
        self.place_button_run()


    def get_root(self):
        return self.__gui

    def get_serial_port(self):
        return self.__serial_port
    
    def set_serial_port(self, serial_port: SerialPort):
        self.__serial_port = serial_port

    def set_grid_settings(self):
        self.__gui.columnconfigure(0, weight=0)
        self.__gui.columnconfigure(1, weight=1)
        self.__gui.columnconfigure(2, weight=1)
        self.__gui.columnconfigure(3, weight=1)
        self.__gui.columnconfigure(4, weight=1)
        self.__gui.columnconfigure(5, weight=1)
        self.__gui.columnconfigure(6, weight=1)
        self.__gui.columnconfigure(7, weight=1)
        self.__gui.columnconfigure(8, weight=1)
        self.__gui.columnconfigure(9, weight=1)

        self.__gui.rowconfigure(0, weight = 1)
        self.__gui.rowconfigure(1, weight=1)
        self.__gui.rowconfigure(2, weight=1)
        self.__gui.rowconfigure(3, weight=1)
        self.__gui.rowconfigure(4, weight=1)
        self.__gui.rowconfigure(5, weight=1)
        self.__gui.rowconfigure(6, weight=1)
        self.__gui.rowconfigure(7, weight=1)
        self.__gui.rowconfigure(8, weight=1)
        self.__gui.rowconfigure(9, weight=1)
        self.__gui.rowconfigure(10, weight=1)
        self.__gui.rowconfigure(10, weight=1)
        self.__gui.rowconfigure(11, weight=1)
        self.__gui.rowconfigure(12, weight=1)

    def place_set_velocity(self):
        self.label_set_velocity.grid(row = 1, column = 0, sticky = 'nse', rowspan=2, pady = 10, padx = 10)
        self.entry_set_velocity.grid(row = 1, column = 1, sticky ='nsew', rowspan=2, pady = 10, padx = 10, columnspan = 2)

        self.label_slider.grid(row=1, column=3, columnspan=3, sticky='nsew', padx = 10)
        self.slider.grid(row = 2, column = 3, columnspan=3, sticky = 'new', padx = 10)


        self.entry_set_velocity.bind("<Return>", self.callback_set_velocity)

    def place_set_acceleration(self):
        self.label_set_acceleration.grid(row = 3, column = 0, sticky='nse', rowspan=2, pady = 10, padx = 10)
        self.entry_set_acceleration.grid(row = 3, column = 1, sticky='nsew', rowspan=2, columnspan=2, pady = 10, padx = 10)
        self.entry_set_acceleration.bind("<Return>", self.callback_set_acceleration)

    def place_timeout(self):
        self.entry_timeout.bind("<Return>", self.callback_timeout)
        self.label_timeout.grid(row=5, column=0, sticky="nse", padx=10, rowspan=2, pady = 10)
        self.entry_timeout.grid(row=5, column=1, sticky="nsew", padx=10, rowspan=2, columnspan=2)

        self.entry_hour.grid(row=5, column=3, rowspan=2, columnspan=2, sticky='nse')
        self.button_hour_up.grid(row=5, column=5, sticky='nsw')
        self.button_hour_down.grid(row=6, column=5, sticky='nsw')

        self.label_time_dott.grid(row=5, column=5, rowspan=2, sticky='nse')

        self.entry_minute.grid(row=5, column=6, rowspan=2, columnspan=2, sticky='nse')

        self.button_minute_up.grid(row = 5, column = 8, sticky='nsw')
        self.button_minute_down.grid(row = 6, column = 8, sticky='nsw')

        self.button_timer_on.grid(row = 5, column = 9, sticky='nsw', padx = 10)
        self.button_save_timer.grid(row = 6, column = 9, sticky='nsw', padx = 10)

    def place_button_run(self):
        self.button_run.grid(row = 2, column = 7, sticky='nsew')

    def callback_save_button(self):
        pass

    def callback_timeout(self, event):
        print("eywa")
        now = datetime.now()
        minute_now = int(now.strftime("%M"))
        hour_now = int(now.strftime("%H"))

        self.timer = int(self.timer_str.get())

        self.timeout_hour = ((self.timer // 60) + hour_now ) % 24

        self.timeout_minute = ((self.timer % 60) + minute_now) % 60

        self.timeout_hour_str.set(f"{self.timeout_hour:02}")
        self.timeout_minute_str.set(f"{self.timeout_minute:02}")

    def callback_hour(self, up: bool):
        if up:
            self.timeout_hour = (self.timeout_hour + 1) % 24
        else:
            self.timeout_hour = (self.timeout_hour - 1) % 24

        self.update_timer()
        self.timeout_hour_str.set(f"{self.timeout_hour:02}")

    def callback_minute(self, up: bool):
        if up:
            self.timeout_minute = (self.timeout_minute + 1) % 60
        else:
            self.timeout_minute = (self.timeout_minute - 1) % 60

        self.update_timer()
        self.timeout_minute_str.set(f"{self.timeout_minute:02}")


    def update_timer(self):
        now = datetime.now()
        minute_now = int(now.strftime("%M"))
        hour_now = int(now.strftime("%H"))
        print(f"timeout_minute {self.timeout_minute}")
        print(f"timeout_hour {self.timeout_hour}")

        timeout = (self.timeout_minute - minute_now) + (self.timeout_hour - hour_now) * 60

        print(timeout)
        if timeout < 0:
            self.timer_str.set("0.00")
            self.timer = 0

        else:
            self.timer_str.set(f"{timeout:.2f}")
            self.timer = timeout

        print(self.timer)

    def callback_timer_on(self):
        if self.doTimer:
            self.doTimer = False
            self.button_timer_on.config(text = "Timer: Off", bootstyle = 'danger')
        else:
            self.doTimer = True
            self.button_timer_on.config(text = "Timer: On", bootstyle = 'success')

    """
    Called by pressing Enter on the Velocity Entry, gets the self.curr_velocity_str value(StringVar) which is binded to
    the velocity Entry widged. Checks if the enterd value is inside of allowed velocity interval. Updates the slider value 
    and the velocity info label above slider. At last the command to set the velocity is send via Serial by the bldc object.
    """
    def callback_set_velocity(self, event):
        if float(self.curr_velocity_str.get()) < self.min_velocity_float:
          self.curr_velocity_float = 0.0
          self.curr_velocity_str.set(str(self.curr_velocity_float))

        elif float(self.curr_velocity_str.get()) > self.max_velocity_float:
            self.curr_velocity_float = self.max_velocity_float
            self.curr_velocity_str.set(str(self.curr_velocity_float))

        else:
            self.curr_velocity_float = float(self.curr_velocity_str.get())

        slider_perc = self.curr_velocity_float / self.max_velocity_float

        self.slider.set(slider_perc)
        #self.bldc.set_velocity(self.curr_velocity_float)

    def callback_run(self):
        if self.runnig:
            self.runnig = False
            self.button_run.config(text = 'Run', bootstyle = 'success')
            self.bldc.run_motor(doRun=True)
        else:
            self.runnig = True
            self.button_run.config(text = 'Stop', bootstyle = 'danger')
            self.bldc.run_motor(doRun=False)

    """
    gets called each time the slider changes and sets up a after call so that after 0.2 sec the actual callback logic gets called
    to prevent from serial spam/serial latency
    """
    def callback_slider(self, val):
        if hasattr(self, "_slider_job"):
            self.__gui.after_cancel(self._slider_job)

        self._slider_job = self.__gui.after(200, lambda: self._apply_slider_value(val))

    """
    Updates velocity entry widget and the label above the slider with the current slider value as percentage of the max 
    allowed velocity(hard coded in init). At last it sends the Serial set velocity command via bldc object 
    """
    def _apply_slider_value(self, val):
        float_perc = float(val)

        velocity_input = float_perc * self.max_velocity_float
        if velocity_input == 0:
            self.curr_velocity_float = 0
        elif velocity_input < self.min_velocity_float:
            self.curr_velocity_float = self.min_velocity_float
        else:
            self.curr_velocity_float = velocity_input

        self.label_slider.config(text=f"Maximum velocity: {self.curr_velocity_float:.2f} rpm")
        self.curr_velocity_str.set(f"{self.curr_velocity_float:.2f}")

        self.bldc.set_velocity(round(self.curr_velocity_float, 2))

    """
    Called by pressing Enter on acceleration Entry, gets the value of curr_acceleration_str (StringVar), which is binded 
    to the Entry 
    """
    def callback_set_acceleration(self, event):
        acceleration_inp = float(self.curr_acceleration_str.get())
        if acceleration_inp > self.max_acceleration:
            self.curr_acceleration_float = self.max_acceleration
        else:
            self.curr_acceleration_float = acceleration_inp
        self.curr_acceleration_str.set(f"{self.curr_acceleration_float:.2f}")
        self.bldc.set_acceleration(self.curr_acceleration_float)

    def callback_settings(self):
        self.toplevel_settings.show()

    def check_timer(self):
        if not self.doTimer:
            return

        now = datetime.now()
        now_hour = now.strftime("%H")
        now_minute = now.strftime("%M")

        if (int(now_hour) >= self.timeout_hour) and int(now_minute) >= self.timeout_minute:
            #self.bldc.run_motor(False)
            print("timeout accured")

    def calculate_min_velocity(self)->float:
        max_timeout_min =  (GUI.MAX_COUNTER * self.prescale / GUI.F_CPU)/60
        return  GUI.DEGREES_PER_PHASE / max_timeout_min

    def calculate_max_velocity(self):
        min_timeout_min =  (1 * self.prescale / GUI.F_CPU)/60
        return GUI.DEGREES_PER_PHASE / min_timeout_min

class Setup:
    STANDARD_FONT = ("Helvetica", 14)
    def __init__(self, main: GUI):
        #initialized after in callback_done
        self.gui = main
        self.__com_port: str

        self.main_root = self.gui.get_root()
        self.__setup = ttk.Toplevel(self.main_root)
        self.__setup.geometry("840x500")
        self.__setup.title("Setup")
        self.__setup.protocol("WM_DELETE_WINDOW", self.withdraw)

        data = read_json()

        self.en1 = StringVar(value = data["en1"])
        self.en2 = StringVar(value = data["en2"])
        self.en3 = StringVar(value = data["en3"])
        self.in1 = StringVar(value = data["in1"])
        self.in2 = StringVar(value = data["in2"])
        self.in3 = StringVar(value = data["in3"])

        self.com_port = StringVar(value = data["com_port"])
        self.prescale_str = StringVar(value = data["prescale"])

        self.frame_pins = ttk.Frame(self.__setup)

        self.label_pins =               ttk.Label(self.__setup, text = "Pins", font = Setup.STANDARD_FONT)
        self.label_en1 =                ttk.Label(self.frame_pins, text = "en1", font=Setup.STANDARD_FONT, anchor="center")
        self.label_en2 =                ttk.Label(self.frame_pins, text = "en2", font=Setup.STANDARD_FONT, anchor="center")
        self.label_en3 =                ttk.Label(self.frame_pins, text = "en3", font=Setup.STANDARD_FONT, anchor="center")
        self.label_in1 =                ttk.Label(self.frame_pins, text = "in1", font=Setup.STANDARD_FONT, anchor="center")
        self.label_in2 =                ttk.Label(self.frame_pins, text = "in2", font=Setup.STANDARD_FONT, anchor="center")
        self.label_in3 =                ttk.Label(self.frame_pins, text = "in3", font=Setup.STANDARD_FONT, anchor="center")

        self.entry_en1 =                ttk.Entry(self.frame_pins, textvariable = self.en1, font=Setup.STANDARD_FONT, justify="center")
        self.entry_en2 =                ttk.Entry(self.frame_pins, textvariable = self.en2, font=Setup.STANDARD_FONT, justify="center")
        self.entry_in1 =                ttk.Entry(self.frame_pins, textvariable = self.in1, font=Setup.STANDARD_FONT, justify="center")
        self.entry_en3 =                ttk.Entry(self.frame_pins, textvariable = self.en3, font=Setup.STANDARD_FONT, justify="center")
        self.entry_in2 =                ttk.Entry(self.frame_pins, textvariable = self.in2, font=Setup.STANDARD_FONT, justify="center")
        self.entry_in3 =                ttk.Entry(self.frame_pins, textvariable = self.in3, font=Setup.STANDARD_FONT, justify="center")

        self.label_com_port = ttk.Label(self.__setup, text = "COM Port", font = Setup.STANDARD_FONT, anchor="center")
        self.entry_com_port = ttk.Entry(self.__setup,textvariable = self.com_port, font = Setup.STANDARD_FONT, justify="center")

        self.label_prescale =           ttk.Label(self.__setup, text = "Prescale", font = Setup.STANDARD_FONT, anchor="center")
        self.entry_prescale =           ttk.Entry(self.__setup, textvariable=self.prescale_str, font = Setup.STANDARD_FONT, justify="center")

        self.button_done =              ttk.Button(self.__setup, text="Done", command=self.callback_done)

        self.place_pin_settings()
        self.place_com_port()
        self.place_prescale()
        self.place_button_done()

    def get_root(self):
        return self.__setup

    def withdraw(self):
        self.__setup.withdraw()

    def show(self):
        self.__setup.deiconify()

    def set_grid_settings(self):
        self.__setup.columnconfigure(0, weight=1)
        self.__setup.columnconfigure(1, weight=1)
        self.__setup.columnconfigure(2, weight=1)
        self.__setup.columnconfigure(3, weight=1)
        self.__setup.columnconfigure(4, weight=1)

        self.__setup.rowconfigure(0, weight=1)
        self.__setup.rowconfigure(1, weight=1)
        self.__setup.rowconfigure(2, weight=1)
        self.__setup.rowconfigure(3, weight=1)

    def place_com_port(self):
        self.label_com_port.grid(row = 0, column = 3, sticky = "nsew", padx = 10, pady = 5)
        self.entry_com_port.grid(row = 1, column = 3, sticky = "nsew", padx = 10, pady = 5)


    def place_prescale(self):
        self.label_prescale.grid(row = 0, column = 4, sticky = "nsew", padx = 10, pady = 5)
        self.entry_prescale.grid(row = 1, column = 4, sticky = "nsew", padx = 10, pady = 5)

    def place_button_done(self):
        self.button_done.grid(row = 3, column = 4,rowspan=2, sticky = "nsew", padx = 10, pady = 5)

    def place_pin_settings(self):
        self.frame_pins.grid(row = 1, column = 0, rowspan=3, columnspan = 2, sticky='nsew')

        self.frame_pins.rowconfigure(0, weight = 1)
        self.frame_pins.rowconfigure(1, weight = 2)
        self.frame_pins.rowconfigure(2, weight = 2)
        self.frame_pins.rowconfigure(3, weight = 2)
        self.frame_pins.rowconfigure(4, weight = 2)
        self.frame_pins.rowconfigure(5, weight = 2)
        self.frame_pins.rowconfigure(6, weight = 2)

        self.frame_pins.columnconfigure(0, weight = 1)
        self.frame_pins.columnconfigure(1, weight = 1)

        self.label_pins.grid(row = 0, column = 0, columnspan=2, pady = 10)

        self.label_en1.grid(row = 1, column = 0, sticky='nse', pady = 5, padx = 10)
        self.label_in1.grid(row = 2, column = 0, sticky='nse', pady = 5, padx = 10)
        self.label_en2.grid(row = 3, column = 0, sticky='nse', pady = 5, padx = 10)
        self.label_in2.grid(row = 4, column = 0, sticky='nse', pady = 5, padx = 10)
        self.label_en3.grid(row = 5, column = 0, sticky='nse', pady = 5, padx = 10)
        self.label_in3.grid(row = 6, column = 0, sticky='nse', pady = 5, padx = 10)

        self.entry_en1.grid(row = 1, column = 1, sticky='nsew', pady = 5, padx = 10)
        self.entry_in1.grid(row = 2, column = 1, sticky='nsew', pady = 5, padx = 10)
        self.entry_en2.grid(row = 3, column = 1, sticky='nsew', pady = 5, padx = 10)
        self.entry_in2.grid(row = 4, column = 1, sticky='nsew', pady = 5, padx = 10)
        self.entry_en3.grid(row = 5, column = 1, sticky='nsew', pady = 5, padx = 10)
        self.entry_in3.grid(row = 6, column = 1, sticky='nsew', pady = 5, padx = 10)

    def callback_done(self):
        """
        Checks if entry inputs are valid, writes setup.json values, initializes SerialPort only if necessary,
        and sends Arduino setup commands via serial, by the bldc object of gui.
        """
        if not (self.en1.get().isdigit()
                and self.en2.get().isdigit()
                and self.en3.get().isdigit()
                and self.in1.get().isdigit()
                and self.in2.get().isdigit()
                and self.in3.get().isdigit()):
            message_box_error("wrong pins")
            return

        write_json("en1", int(self.en1.get()))
        write_json("en2", int(self.en2.get()))
        write_json("en3", int(self.en3.get()))
        write_json("in1", int(self.in1.get()))
        write_json("in2", int(self.in2.get()))
        write_json("in3", int(self.in3.get()))

        if not self.prescale_str.get().isdigit():
            message_box_error("wrong prescale")
            return

        write_json("prescale", self.prescale_str.get())
        self.gui.prescale=int(self.prescale_str.get())
        self.gui.min_velocity_float = self.gui.calculate_min_velocity()

        #port inside the entry widget
        current_port = int(self.com_port.get())

        #serial port needs init
        if self.gui.get_serial_port() is None:
            try:
                serial_port = SerialPort(current_port)
                self.gui.set_serial_port(serial_port=serial_port)
                write_json("com_port", current_port)

            except SerialException as e:
                if "FileNotFoundError" in str(e):
                    message_box_error(error="not found")
                elif "PermissionError" in str(e):
                    message_box_error(error="no permission")
                return
            except Exception:
                message_box_error(error="unexpected error")
                return

        #close old port and open new one
        if self.gui.get_serial_port().get_port() != current_port:
            try:
                self.gui.get_serial_port().close_serial()
                serial_port = SerialPort(current_port)
                self.gui.set_serial_port(serial_port=serial_port)
                write_json("com_port", current_port)

            except SerialException as e:
                if "FileNotFoundError" in str(e):
                    message_box_error(error="not found")
                elif "PermissionError" in str(e):
                    message_box_error(error="no permission")
                return

            except Exception:
                message_box_error(error="unexpected error")
                return

        self.gui.bldc = BLDC(serial_port=self.gui.get_serial_port())
        self.gui.bldc.basic_setup_routine()

        self.__setup.withdraw()
        self.main_root.deiconify()

gui = GUI()
root = gui.get_root()
root.mainloop()