import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.toast import ToastNotification
import tkinter as tk
import serial
import serial.tools.list_ports
import json
import ast
import os
from datetime import datetime
import pygame
from globalvar import GlobalConfig

class ScaleFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)

        pygame.mixer.init()

        current_date = datetime.now().strftime("%Y-%m-%d")

        self.last_part = tk.StringVar()
        self.part = tk.StringVar()
        self.std = tk.StringVar()
        self.weight = tk.DoubleVar(value=0.00)
        self.scale = tk.StringVar()
        self.last_check = tk.IntVar(value=0)

        self.flag_tare = tk.BooleanVar(value=False)

        self.popups = {
            "com": None,
            "part": None
        }
        
        GlobalConfig.select_com_options = GlobalConfig.get_available_com_ports()
        
        self.select_part_options = []

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)
        self.grid_rowconfigure(5, weight=0)
        self.grid_columnconfigure(0, weight=1, minsize=100)
        self.grid_columnconfigure(1, weight=1, minsize=100)
        self.grid_columnconfigure(2, weight=1, minsize=100)
        self.grid_columnconfigure(3, weight=1, minsize=100)

        self.select_com_combobox = ttk.Menubutton(
            master=self,
            text="SELECT COM PORT",
            bootstyle=SECONDARY,
            state="readonly",
        )
        self.select_com_combobox.grid(row=0, column=0, columnspan=2, sticky=NSEW, ipady=10, padx=5, pady=5)
        self.select_com_combobox.bind('<Button-1>', lambda event: self.toggle_popup("com", self.select_com_combobox, GlobalConfig.select_com_options, GlobalConfig.com_port))

        self.connect_button = ttk.Button(
            master=self,
            text='CONNECT',
            bootstyle=INFO,
            command=self.toggle_connect
        )
        self.connect_button.grid(row=1, column=0, columnspan=2, sticky=NSEW, ipady=10, padx=5, pady=5)

        self.select_part_combobox = ttk.Menubutton(
            master=self,
            text="SELECT PART",
            bootstyle=SECONDARY,
            state="disabled",
        )
        self.select_part_combobox.grid(row=2, column=0, columnspan=2, sticky=NSEW, ipady=10, padx=5, pady=5)
        self.select_part_combobox.bind('<Button-1>', lambda event: self.toggle_popup("part", self.select_part_combobox, self.select_part_options, self.part))

        self.create_popup(self.select_com_combobox, "com", GlobalConfig.select_com_options, GlobalConfig.com_port)
        self.create_popup(self.select_part_combobox, "part", self.select_part_options, self.part)

        status_label_frame = ttk.Labelframe(self, text='STATUS')
        status_label_frame.grid(row=0, column=2, rowspan=2, columnspan=2, sticky=NSEW, padx=5, pady=5)
        status_label_frame.grid_rowconfigure(0, weight=0)
        status_label_frame.grid_rowconfigure(1, weight=0)
        status_label_frame.grid_rowconfigure(2, weight=0)
        status_label_frame.grid_columnconfigure(0, weight=1)

        self.status_count_label = ttk.Label(status_label_frame, text="0", justify=RIGHT, anchor=E, font=('Segoe UI', 48))
        self.status_count_label.grid(row=0, sticky=EW, padx=15)

        status_date_label = ttk.Label(status_label_frame, text=current_date, justify=LEFT, anchor=W,  font=('Segoe UI', 18))
        status_date_label.grid(row=1, sticky=SW, padx=5, pady=(0,5))
        
        status_label = ttk.Label(status_label_frame, text="Packages", justify=RIGHT, anchor=E, font=('Segoe UI', 18))
        status_label.grid(row=1, sticky=SE, padx=15, pady=(0, 5))

        self.reload_button = ttk.Button(
            master=self,
            text='RELOAD',
            bootstyle=INFO,
            state=DISABLED,
            command=self.handle_get_parts
        )
        self.reload_button.grid(row=2, column=2, sticky=NSEW, ipady=10, padx=5, pady=5)

        self.tare_button = ttk.Button(
            master=self,
            text='TARE',
            bootstyle=INFO,
            state=DISABLED,
            command=self.handle_tare
        )
        self.tare_button.grid(row=2, column=3, sticky=NSEW, ipady=10, padx=5, pady=5)

        self.std_label = ttk.Label(self, textvariable=self.std, justify=RIGHT, anchor=E, font=('Segoe UI', 24))
        self.std_label.grid(row=3, column=0, columnspan=4, sticky=NSEW, padx=15, pady=(15,5))
        
        self.weight_label = ttk.Label(self, textvariable=self.scale, justify=RIGHT, anchor=E, font=('Segoe UI', 96))
        self.weight_label.grid(row=4, column=0, columnspan=4, sticky=NSEW, padx=15, pady=5)

        self.check_label = ttk.Label(self, justify=RIGHT, anchor=E, font=('Arial', 56))
        self.check_label.grid(row=5, column=0, columnspan=4, sticky=NSEW, padx=15, pady=5)

        self.update_com_ports()

        if GlobalConfig.serial_connection and GlobalConfig.serial_connection.is_open:
            self.select_com_combobox.config(text=GlobalConfig.com_port)
            self.toggle_connect()

    def create_popup(self, widget, popup_key, options, variable):
        if self.popups[popup_key] is not None:
            self.popups[popup_key].destroy()

        popup = tk.Toplevel(self)
        popup.title('')
        popup.withdraw()

        x = widget.winfo_rootx()
        y = widget.winfo_rooty() + widget.winfo_height()
        popup.geometry(f"+{x}+{y}")
        popup.bind('<FocusOut>', lambda event: self.hide_popup(popup_key))

        frame = ScrolledFrame(popup)
        frame.pack(fill=tk.BOTH, expand=True, ipadx=5)

        self.create_popup_options(widget, popup, frame, options, variable)

        self.popups[popup_key] = popup

    def create_popup_options(self, widget, popup, frame, options, variable):
        for option in options:
            button = ttk.Button(
                frame,
                text=option["name"] if isinstance(option, dict) else option,
                bootstyle=SECONDARY,
                command=lambda opt=option: self.select_option(widget, popup, opt, variable)
            )
            button.pack(fill=tk.X, ipady=8, pady=5)

    def toggle_popup(self, popup_key, widget, options, variable, event=None):
        state = str(widget.cget("state"))
        if state == "disabled":
            return

        popup = self.popups[popup_key]

        if popup is None or not popup.winfo_exists():
            self.create_popup(widget, popup_key, options, variable)
            popup = self.popups[popup_key]

        if popup.winfo_viewable():
            popup.withdraw()
        else:
            x = widget.winfo_rootx()
            y = widget.winfo_rooty() + widget.winfo_height() + 10
            popup.geometry(f"+{x}+{y}")

            popup.deiconify()
            popup.lift()
            popup.focus_set()

    def hide_popup(self, popup_key, event=None):
        if self.popups[popup_key]:
            self.popups[popup_key].destroy()
            self.popups[popup_key] = None

    def select_option(self, widget, popup, option, variable):
        if isinstance(variable, tk.StringVar):
            variable.set(option)
        else:
            GlobalConfig.com_port = option

        if isinstance(option, dict) and "name" in option:
            widget.config(text=option["name"])
        else:
            widget.config(text=option)
        popup.destroy()

    def update_com_ports(self):
        # Check if the connect_button text is "CONNECT"
        if self.connect_button.cget("text") == "CONNECT":
            new_com_ports = GlobalConfig.get_available_com_ports()
            if new_com_ports != GlobalConfig.select_com_options:
                GlobalConfig.select_com_options = new_com_ports
                
                # Update the popup if it's currently visible
                if self.popups["com"] and self.popups["com"].winfo_exists():
                    self.create_popup(self.select_com_combobox, "com", GlobalConfig.select_com_options, GlobalConfig.com_port)
        # Schedule the next update
        self.after(1000, self.update_com_ports)  # Update every second

    def get_parts(self):
        if GlobalConfig.serial_connection and GlobalConfig.serial_connection.is_open:
            request = {
                "cmd": 1
            }
            if GlobalConfig.send_request(request):
                str_response = GlobalConfig.read_response()
                if str_response:
                    return GlobalConfig.parse_json(str_response)
        else:
            print("Serial connection is not open.")
        return None

    def refresh_data_set(self):
        if GlobalConfig.serial_connection and GlobalConfig.serial_connection.is_open:
            request = {
                "cmd": 12
            }
            if GlobalConfig.send_request(request):
                str_response = GlobalConfig.read_response()
                if str_response:
                    return GlobalConfig.parse_json(str_response)
        else:
            print("Serial connection is not open.")
        return None

    def tare(self):
        if GlobalConfig.serial_connection and GlobalConfig.serial_connection.is_open:
            request = {
                "cmd": 7
            }
            if GlobalConfig.send_request(request):
                str_response = GlobalConfig.read_response()
                if str_response:
                    return GlobalConfig.parse_json(str_response)
        else:
            print("Serial connection is not open.")
        return None

    def get_weight(self, std, unit, hysteresis):
        if GlobalConfig.serial_connection and GlobalConfig.serial_connection.is_open:
            request = {
                "cmd": 8,
                "data": {
                    "std": std,
                    "unit": unit,
                    "hysteresis": hysteresis
                }
            }
            if GlobalConfig.send_request(request):
                str_response = GlobalConfig.read_response()
                if str_response:
                    return GlobalConfig.parse_json(str_response)
        else:
            print("Serial connection is not open.")
        return None

    def toggle_connect(self):
        current_text = self.connect_button.cget("text")
        if current_text == "CONNECT":
            if GlobalConfig.com_port == "":
                return

            if self.connect_to_com_port():
                self.connect_button.config(text="DISCONNECT", bootstyle="DANGER")
                self.select_com_combobox.config(state=DISABLED)
                self.select_part_combobox.config(state=READONLY)
                self.reload_button.config(state=NORMAL)
                self.tare_button.config(state=NORMAL)
                self.handle_get_parts()
                self.update_scale()
        else:
            if self.disconnect_from_com_port():
                self.connect_button.config(text="CONNECT", bootstyle="INFO")
                self.select_com_combobox.config(state=READONLY)
                self.select_part_combobox.config(state=DISABLED)
                self.reload_button.config(state=DISABLED)
                self.tare_button.config(state=DISABLED)

                self.last_check.set(0)
                self.std.set("")
                self.scale.set("")
                self.check_label.config(text="")

                self.part.set("")
                self.select_part_combobox.config(text="SELECT PART")

    def connect_to_com_port(self):
          # Reference the global variable
        try:
            GlobalConfig.serial_connection = serial.Serial(GlobalConfig.com_port, 115200, timeout=1)
            return True
        except Exception as e:
            self.notificatiion("OPEN PORT", f"Failed to connect to {GlobalConfig.com_port}: {e}", False)
            return False

    def disconnect_from_com_port(self):
          # Reference the global variable
        if GlobalConfig.serial_connection and GlobalConfig.serial_connection.is_open:
            GlobalConfig.serial_connection.close()
            GlobalConfig.serial_connection = None
            return True
        return False

    def notificatiion(self, title, message, status):
        toast = ToastNotification(
            title=title,
            message=message,
            duration=1500,
            bootstyle=SUCCESS if status else DANGER,
            position=(self.winfo_rootx(), self.winfo_rooty(), NW)
        )
        toast.show_toast()

    def handle_get_parts(self):
        try:
            response = self.get_parts()
            if response['status'] == 200:
                self.notificatiion("Get Parts", response['message'], True)
                self.select_part_options = response['data']
                
                self.create_popup(self.select_part_combobox, "part", self.select_part_options, self.part)
            else:
                self.notificatiion("Get Parts", response['message'], False)
        except Exception as e:
            self.notificatiion("Get Parts", f"An error occurred: {e}", False)

    def handle_refresh_data_set(self):
        try:
            response = self.refresh_data_set()
            if response['status'] == 200:
                self.notificatiion("Refresh Data Set", response['message'], True)
            else:
                self.notificatiion("Refresh Data Set", response['message'], False)
        except Exception as e:
            self.notificatiion("Refresh Data Set", f"An error occurred: {e}", False)

    def handle_tare(self):
        self.flag_tare.set(True)

        try:
            response = self.tare()
            if response['status'] == 200:
                self.flag_tare.set(False)
                self.notificatiion("Tare Status", response['message'], True)
                
            else:
                self.flag_tare.set(False)
                self.notificatiion("Tare Status", response['message'], False)
        except Exception as e:
            self.flag_tare.set(False)
            self.notificatiion("Tare Status", f"An error occurred: {e}", False)

    def update_scale(self):
        if self.connect_button.cget("text") == "DISCONNECT" and self.flag_tare.get() == False:
            try:
                if self.part.get() != "":
                    part = ast.literal_eval(self.part.get())

                    if self.last_part.get() != self.part.get():
                        self.handle_refresh_data_set()
                        self.last_part.set(self.part.get())
                        self.std.set(f"Standard Weight: {part['std']} {part['unit']}, Hysteresis: {part['hysteresis']:.2f}")

                    
                    response = self.get_weight(part["std"], part["unit"], part["hysteresis"])
                    if response['status'] == 200:
                        weight = response['data']['weight']
                        check = response['data']['check']

                        if part['unit'] == 'kg':
                            scale = f"{float(format(weight, '.2f'))} {part['unit']}"
                        else:
                            scale = f"{int(weight)} {part['unit']}"

                        if check == 1 and check != self.last_check.get():
                            self.play_tone("OK")
                            self.check_label.config(foreground='green')
                            self.check_label.config(text="QTY GOOD")
                        elif check == 2 and check != self.last_check.get():
                            self.play_tone("NG")
                            self.check_label.config(foreground='red')
                            self.check_label.config(text="NOT GOOD")
                        elif check == 0 and check != self.last_check.get():
                            self.check_label.config(text="")
                        
                        self.last_check.set(check)
                        self.scale.set(scale)
                        self.weight_label.config(text=scale)
            except Exception as e:
                print(f"An error occurred: {e}")

        # Schedule the next update
        self.after(100, self.update_scale)  # Update every second

    def validate_numeric_input(self, action, value_if_allowed, text):
        if action == '1':
            return text.isdigit() and int(value_if_allowed) > 0
        return True
    
    def play_tone(self, status):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        filename = ""
        if status == "OK":
            filename = "OK.mp3"
        elif status == "NG":
            filename = "NG.mp3"
        sound_path = os.path.join(current_dir, "assets", "tone", filename)
        pygame.mixer.music.load(sound_path)
        pygame.mixer.music.play()