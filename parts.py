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
import pygame
from globalvar import GlobalConfig
from collapsingframe import CollapsingFrame

class PartsFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)

        self.popups = {
            "com": None
        }
        
        GlobalConfig.select_com_options = GlobalConfig.get_available_com_ports()

        self.parts = []

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)
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
        self.create_popup(self.select_com_combobox, "com", GlobalConfig.select_com_options, GlobalConfig.com_port)

        self.connect_button = ttk.Button(
            master=self,
            text='CONNECT',
            bootstyle=INFO,
            command=self.toggle_connect
        )
        self.connect_button.grid(row=1, column=0, columnspan=2, sticky=NSEW, ipady=10, padx=5, pady=5)

        status_label_frame = ttk.Labelframe(self, text='STATUS')
        status_label_frame.grid(row=0, column=2, rowspan=2, columnspan=2, sticky=NSEW, padx=5, pady=5)

        self.reload_button = ttk.Button(
            master=self,
            text='RELOAD',
            bootstyle=INFO,
            state=DISABLED,
            command=self.handle_get_parts
        )
        self.reload_button.grid(row=2, column=2, sticky=NSEW, ipady=10, padx=5, pady=5)

        self.create_button = ttk.Button(
            master=self,
            text='CREATE',
            bootstyle=SUCCESS,
            state=DISABLED,
            # command=self.open_dialog
        )
        self.create_button.grid(row=2, column=3, sticky=NSEW, ipady=10, padx=5, pady=5)
        
        self.cf = CollapsingFrame(self)
        self.cf.grid(row=3, column=0, columnspan=4, sticky=NSEW, padx=5, pady=5)

        for part in self.parts:
            group = ttk.Frame(self.cf, padding=10)
            # for x in range(5):
            #     ttk.Checkbutton(group1, text=f'Option {x + 1}').pack(fill=X)
            self.cf.add(child=group, title=part['name'], subtitle=f"{part['std']} {part['unit']}")

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

    def toggle_connect(self):
        current_text = self.connect_button.cget("text")
        if current_text == "CONNECT":
            if GlobalConfig.com_port == "":
                return

            if self.connect_to_com_port():
                self.connect_button.config(text="DISCONNECT", bootstyle="DANGER")
                self.select_com_combobox.config(state=DISABLED)
                
                self.reload_button.config(state=NORMAL)
                self.create_button.config(state=NORMAL)
                # self.tare_button.config(state=NORMAL)
                self.handle_get_parts()
                
        else:
            if self.disconnect_from_com_port():
                self.connect_button.config(text="CONNECT", bootstyle="INFO")
                self.select_com_combobox.config(state=READONLY)
                
                self.reload_button.config(state=DISABLED)
                self.create_button.config(state=DISABLED)
                # self.tare_button.config(state=DISABLED)

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

    def create_part(self, name, std, unit):
        if GlobalConfig.serial_connection and GlobalConfig.serial_connection.is_open:
            request = {
                "cmd": 4,
                "data": {
                    "name": name,
                    "std": std,
                    "unit": unit
                }
            }
            if GlobalConfig.send_request(request):
                str_response = GlobalConfig.read_response()
                if str_response:
                    return GlobalConfig.parse_json(str_response)
        else:
            print("Serial connection is not open.")
        return None

    def update_part(self, id, name, std, unit):
        if GlobalConfig.serial_connection and GlobalConfig.serial_connection.is_open:
            request = {
                "cmd": 5,
                "data": {
                    "id": id,
                    "name": name,
                    "std": std,
                    "unit": unit
                }
            }
            if GlobalConfig.send_request(request):
                str_response = GlobalConfig.read_response()
                if str_response:
                    return GlobalConfig.parse_json(str_response)
        else:
            print("Serial connection is not open.")
        return None

    def delete_part(self, id):
        if GlobalConfig.serial_connection and GlobalConfig.serial_connection.is_open:
            request = {
                "cmd": 6,
                "data": id
            }
            if GlobalConfig.send_request(request):
                str_response = GlobalConfig.read_response()
                if str_response:
                    return GlobalConfig.parse_json(str_response)
        else:
            print("Serial connection is not open.")
        return None

    def connect_to_com_port(self):
        try:
            GlobalConfig.serial_connection = serial.Serial(GlobalConfig.com_port, 115200, timeout=1)
            return True
        except Exception as e:
            self.notificatiion("OPEN PORT", f"Failed to connect to {GlobalConfig.com_port}: {e}", False)
            return False

    def disconnect_from_com_port(self):
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
                self.parts = response['data']
                
                for child in self.cf.winfo_children():
                    child.destroy()

                for part in self.parts:
                    group = ttk.Frame(self.cf, padding=10, bootstyle=DARK)
                    ttk.Button(group, text="MODIFY").pack(side=RIGHT, padx=5)
                    ttk.Button(group, text="DELETE").pack(side=RIGHT, padx=5)
                    # for x in range(5):
                    #     ttk.Checkbutton(group1, text=f'Option {x + 1}').pack(fill=X)
                    self.cf.add(child=group, title=f"{part['name']}\n{part['std']} {part['unit']}")
                # self.create_popup(self.select_part_combobox, "part", self.select_part_options, self.part)
            else:
                self.notificatiion("Get Parts", response['message'], False)
        except Exception as e:
            self.notificatiion("Get Parts", f"An error occurred: {e}", False)




