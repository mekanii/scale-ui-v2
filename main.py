from pathlib import Path
from PIL import Image
Image.CUBIC = Image.BICUBIC

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
import tkinter as tk
import serial
import serial.tools.list_ports
import json
import ast

import os
import asyncio
import threading
import pygame

PATH = Path(__file__).parent / 'assets'

class Main(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.pack(expand=True, fill=BOTH)

        self.images = [
            ttk.PhotoImage(
                name='package-36',
                file=PATH / 'icons/package-36.png'),
            ttk.PhotoImage(
                name='device-36',
                file=PATH / 'icons/device-36.png'),
            ttk.PhotoImage(
                name='cog-36',
                file=PATH / 'icons/cog-36.png')
        ]

        style = ttk.Style()

        style.configure('Secondary.TLabelframe', background=style.colors.secondary)
        style.configure('Secondary.TLabel', background=style.colors.secondary)
        style.configure('Padx.TEntry', padding=(10, 0))
        style.configure('Padding.TCombobox', padding=(10, 15))
        
        self.menu_selected = tk.StringVar(value='main')

        self.status_run = tk.BooleanVar(value=True)
        self.status_run_text = tk.StringVar(value='STOP')
        self.status_run_bootstyle = 'square-toggle-danger'

        self.com_port = tk.StringVar()
        self.part = tk.StringVar()

        self.weight = tk.DoubleVar(value=0.00)
        self.scale = tk.StringVar()
        self.last_check = tk.IntVar(value=0)

        self.serial_connection = None

        v_numeric_cmd = (self.register(self.validate_numeric_input), '%d', '%P', '%S')

        # menu buttons
        menu_frame = ttk.Frame(self, bootstyle=SECONDARY)
        menu_frame.grid(row=0, column=0, sticky=NS)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        menu_main_btn = ttk.Radiobutton(
            master=menu_frame,
            image='package-36',
            text='MAIN',
            value='main',
            variable=self.menu_selected,
            compound=TOP,
            bootstyle=TOOLBUTTON,
            command=lambda: self.change_menu('main')
        )
        menu_main_btn.pack(side=TOP, fill=BOTH, ipady=10)

        menu_parts_btn = ttk.Radiobutton(
            master=menu_frame,
            image='device-36',
            text='PARTS',
            value='parts',
            variable=self.menu_selected,
            compound=TOP,
            bootstyle=TOOLBUTTON,
            command=lambda: self.change_menu('parts')
        )
        menu_parts_btn.pack(side=TOP, fill=BOTH, ipady=10)

        menu_setting_btn = ttk.Radiobutton(
            master=menu_frame,
            image='cog-36',
            text='SETTINGS',
            value='settings',
            variable=self.menu_selected,
            compound=TOP,
            bootstyle=TOOLBUTTON,
            command=lambda: self.change_menu('settings')
        )
        menu_setting_btn.pack(side=TOP, fill=BOTH, ipady=10)

        content_frame = ttk.Frame(self)
        content_frame.grid(row=0, column=1, sticky=NSEW, padx=5, pady=5)
        content_frame.grid_rowconfigure(0, weight=0)
        content_frame.grid_rowconfigure(1, weight=0)
        content_frame.grid_rowconfigure(2, weight=0)
        content_frame.grid_rowconfigure(3, weight=0)
        content_frame.grid_rowconfigure(4, weight=0)
        content_frame.grid_columnconfigure(0, weight=1, minsize=100)
        content_frame.grid_columnconfigure(1, weight=1, minsize=100)
        content_frame.grid_columnconfigure(2, weight=1, minsize=100)
        content_frame.grid_columnconfigure(3, weight=1, minsize=100)

        # Create the popup window but keep it hidden initially
        self.popups = {
            "com": None,
            "part": None
        }

        select_part_options = [
            {"id": 1, "name": "PART 01", "std": 100, "unit": "gr"},
            {"id": 2, "name": "PART 02", "std": 200, "unit": "gr"},
            {"id": 3, "name": "PART 03", "std": 300, "unit": "gr"},
            {"id": 4, "name": "vivo y95", "std": 163, "unit": "gr"},
            {"id": 5, "name": "Cokelat", "std": 23, "unit": "gr"},
            {"id": 6, "name": "Gula", "std": 1.00, "unit": "kg"},
        ]

        # Dynamically populate select_com_options with available COM ports
        self.select_com_options = self.get_available_com_ports()

        self.select_com_combobox = ttk.Menubutton(
            master=content_frame,
            text="SELECT COM PORT",
            bootstyle=SECONDARY,
            state="readonly",
        )
        self.select_com_combobox.grid(row=0, column=0, columnspan=2, sticky=NSEW, ipady=10, padx=5, pady=5)
        self.select_com_combobox.bind('<Button-1>', lambda event: self.toggle_popup("com", self.select_com_combobox, self.select_com_options, self.com_port))

        self.connect_button = ttk.Button(
            master=content_frame,
            text='CONNECT',
            bootstyle=INFO,
            command=self.toggle_connect
        )
        self.connect_button.grid(row=1, column=0, columnspan=2, sticky=NSEW, ipady=10, padx=5, pady=5)

        self.select_part_combobox = ttk.Menubutton(
            master=content_frame,
            text="SELECT PART",
            bootstyle=SECONDARY,
            state="disabled",
        )
        self.select_part_combobox.grid(row=2, column=0, columnspan=2, sticky=NSEW, ipady=10, padx=5, pady=5)
        self.select_part_combobox.bind('<Button-1>', lambda event: self.toggle_popup("part", self.select_part_combobox, select_part_options, self.part))

        self.create_popup(self.select_com_combobox, "com", self.select_com_options, self.com_port)
        self.create_popup(self.select_part_combobox, "part", select_part_options, self.part)

        status_labelframe = ttk.Labelframe(content_frame, text='STATUS')
        status_labelframe.grid(row=0, column=2, columnspan=2, sticky=NSEW, padx=5, pady=5)

        self.weight_label = ttk.Label(content_frame, textvariable=self.scale, justify=RIGHT, anchor=E, font=('Arial', 96))
        # self.weight_label = ttk.Label(content_frame, text='', justify=RIGHT, anchor=E, font=('Arial', 96))
        self.weight_label.grid(row=3, column=0, columnspan=4, sticky=NSEW, padx=15, pady=5)

        self.status_label = ttk.Label(content_frame, justify=RIGHT, anchor=E, font=('Arial', 56))
        self.status_label.grid(row=4, column=0, columnspan=4, sticky=NSEW, padx=15, pady=5)

        self.update_com_ports()

    def change_menu(self, value):
        self.menu_selected.set(value)

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
        variable.set(option)
        if isinstance(option, dict) and "name" in option:
            widget.config(text=option["name"])
        else:
            widget.config(text=option)
        popup.destroy()

    def get_available_com_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports if 'USB' in port.description or 'Arduino' in port.description]

    def update_com_ports(self):
        # Check if the connect_button text is "CONNECT"
        if self.connect_button.cget("text") == "CONNECT":
            new_com_ports = self.get_available_com_ports()
            if new_com_ports != self.select_com_options:
                self.select_com_options = new_com_ports
                # Update the popup if it's currently visible
                if self.popups["com"] and self.popups["com"].winfo_exists():
                    self.create_popup(self.select_com_combobox, "com", self.select_com_options, self.com_port)
        # Schedule the next update
        self.after(1000, self.update_com_ports)  # Update every second

    def send_request(self, request):
        try:
            str_request = json.dumps(request) + '\n'
            self.serial_connection.write(str_request.encode('utf-8'))
            # print(f"Sent: {str_request.strip()}")
        except Exception as e:
            print(f"Failed to send data: {e}")
            return False
        return True

    def read_response(self):
        try:
            str_response = self.serial_connection.readline().decode('utf-8').strip()
            # print(f"Received: {str_response}")
            return str_response
        except Exception as e:
            print(f"Failed to read data: {e}")
            return None

    def parse_json(self, str_response):
        try:
            response = json.loads(str_response)
            # print(f"Parsed JSON: {response}")
            return response
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON: {e}")
        return None

    def get_parts(self):
        if self.serial_connection and self.serial_connection.is_open:
            request = {
                "cmd": 1,
                "data": ''
            }
            if self.send_request(request):
                str_response = self.read_response()
                if str_response:
                    return self.parse_json(str_response)
        else:
            print("Serial connection is not open.")
        return None

    def create_part(self, name, std, unit):
        if self.serial_connection and self.serial_connection.is_open:
            request = {
                "cmd": 4,
                "data": {
                    "name": name,
                    "std": std,
                    "unit": unit
                }
            }
            if self.send_request(request):
                str_response = self.read_response()
                if str_response:
                    return self.parse_json(str_response)
        else:
            print("Serial connection is not open.")
        return None

    def update_part(self, id, name, std, unit):
        if self.serial_connection and self.serial_connection.is_open:
            request = {
                "cmd": 5,
                "data": {
                    "id": id,
                    "name": name,
                    "std": std,
                    "unit": unit
                }
            }
            if self.send_request(request):
                str_response = self.read_response()
                if str_response:
                    return self.parse_json(str_response)
        else:
            print("Serial connection is not open.")
        return None

    def delete_part(self, id):
        if self.serial_connection and self.serial_connection.is_open:
            request = {
                "cmd": 6,
                "data": id
            }
            if self.send_request(request):
                str_response = self.read_response()
                if str_response:
                    return self.parse_json(str_response)
        else:
            print("Serial connection is not open.")
        return None

    def get_weight(self, std, unit):
        if self.serial_connection and self.serial_connection.is_open:
            request = {
                "cmd": 8,
                "data": {
                    "std": std,
                    "unit": unit
                }
            }
            if self.send_request(request):
                str_response = self.read_response()
                if str_response:
                    return self.parse_json(str_response)
        else:
            print("Serial connection is not open.")
        return None

    def toggle_connect(self):
        current_text = self.connect_button.cget("text")
        if current_text == "CONNECT":
            if self.com_port.get() == "":
                return

            if self.connect_to_com_port():
                self.connect_button.config(text="DISCONNECT", bootstyle="DANGER")
                self.select_com_combobox.config(state="disabled")
                self.select_part_combobox.config(state="readonly")
                self.update_scale()
        else:
            if self.disconnect_from_com_port():
                self.connect_button.config(text="CONNECT", bootstyle="INFO")
                self.select_com_combobox.config(state="readonly")
                self.select_part_combobox.config(state="disabled")
                self.scale.set("")

    def connect_to_com_port(self):
        try:
            self.serial_connection = serial.Serial(self.com_port.get(), 115200, timeout=1)
            return True
        except Exception as e:
            print(f"Failed to connect to {self.com_port.get()}: {e}")
            return False

    def disconnect_from_com_port(self):
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            return True
        return False

    def update_scale(self):
        if self.connect_button.cget("text") == "DISCONNECT":
            if self.part.get() != "":
                part = ast.literal_eval(self.part.get())
                
                response = self.get_weight(part["std"], part["unit"])
                if response['status'] == 200:
                    weight = response['data']['weight']
                    check = response['data']['check']

                    if part['unit'] == 'kg':
                        scale = f"{float(format(weight, '.2f'))} {part['unit']}"
                    else:
                        scale = f"{int(weight)} {part['unit']}"

                    if check == 1 and check != self.last_check.get():
                        # self.play_tone("OK")
                        self.status_label.config(foreground='green')
                        self.status_label.config(text="QTY GOOD")
                    elif check == 2 and check != self.last_check.get():
                        # self.play_tone("NG")
                        self.status_label.config(foreground='red')
                        self.status_label.config(text="NOT GOOD")
                    elif check == 0 and check != self.last_check.get():
                        self.status_label.config(text="")
                    
                    self.last_check.set(check)
                    self.scale.set(scale)
                    self.weight_label.config(text=scale)

        # Schedule the next update
        self.after(50, self.update_scale)  # Update every second

    def validate_numeric_input(self, action, value_if_allowed, text):
        if action == '1':
            return text.isdigit() and int(value_if_allowed) > 0
        return True
    
    async def play_tone(self, status):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        filename = ""
        if status == "OK":
            filename = "OK.mp3"
        elif status == "NG":
            filename = "NG.mp3"
        sound_path = os.path.join(current_dir, "assets", "tone", filename)
        pygame.mixer.music.load(sound_path)
        pygame.mixer.music.play()

if __name__ == "__main__":
    app = ttk.Window("Conveyor", "darkly")
    app.geometry("800x600") 
    Main(app)
    app.mainloop()