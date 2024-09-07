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
import time
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
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1, minsize=100)
        self.grid_columnconfigure(1, weight=1, minsize=100)
        self.grid_columnconfigure(2, weight=1, minsize=100)
        self.grid_columnconfigure(3, weight=1, minsize=100)
        self.grid_columnconfigure(4, weight=1, minsize=100)
        self.grid_columnconfigure(5, weight=1, minsize=100)

        ttk.Label(
            self, 
            text="Parts Standard", 
            font=('Segoe UI', 42)
        ).grid(row=0, column=0, columnspan=2, sticky=NSEW, padx=5, pady=(10, 20))

        self.create_button = ttk.Button(
            master=self,
            image='add-circle-36',
            text='Add Part Standard',
            bootstyle=SUCCESS,
            state=NORMAL,
            command=self.open_dialog
        )
        self.create_button.grid(row=1, column=0, columnspan=2, sticky=NSEW, ipady=10, padx=20, pady=5)

        self.reload_button = ttk.Button(
            master=self,
            image='sync-36',
            text='Reload',
            bootstyle=INFO,
            state=NORMAL,
            command=self.handle_get_parts
        )
        self.reload_button.grid(row=2, column=0, columnspan=2, sticky=NSEW, ipady=10, padx=20, pady=5)
        
        self.status_count_label = ttk.Label(self, text="Found 0 parts", font=('Segoe UI', 24))
        self.status_count_label.grid(row=3, column=0, columnspan=2, sticky=NSEW, padx=20, pady=(20, 5))

        self.scrolled_frame = ScrolledFrame(self)
        self.scrolled_frame.grid(row=4, column=0, columnspan=7, sticky=NSEW)

        # self.open_dialog()

        self.handle_get_parts()

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

    def create_part(self, name, std, unit, hysteresis):
        if GlobalConfig.serial_connection and GlobalConfig.serial_connection.is_open:
            request = {
                "cmd": 4,
                "data": {
                    "name": name,
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

    def update_part(self, id, name, std, unit, hysteresis):
        if GlobalConfig.serial_connection and GlobalConfig.serial_connection.is_open:
            request = {
                "cmd": 5,
                "data": {
                    "id": id,
                    "name": name,
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

    def delete_part(self, id):
        if GlobalConfig.serial_connection and GlobalConfig.serial_connection.is_open:
            request = {
                "cmd": 6,
                "data": {
                    "id": id
                }
            }
            if GlobalConfig.send_request(request):
                str_response = GlobalConfig.read_response()
                if str_response:
                    return GlobalConfig.parse_json(str_response)
        else:
            print("Serial connection is not open.")
        return None

    def get_stable_weight(self):
        if GlobalConfig.serial_connection and GlobalConfig.serial_connection.is_open:
            request = {
                "cmd": 9
            }
            if GlobalConfig.send_request(request):
                str_response = GlobalConfig.read_response()
                if str_response:
                    return GlobalConfig.parse_json(str_response)
        else:
            print("Serial connection is not open.")
        return None

    def connect_to_com_port(self):
        if GlobalConfig.serial_connection and GlobalConfig.serial_connection.is_open:
           return True
        try:
            GlobalConfig.serial_connection = serial.Serial(GlobalConfig.com_port, GlobalConfig.baud_rate, timeout=1)
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
                
                for child in self.scrolled_frame.winfo_children():
                    child.destroy()
                
                self.status_count_label.config(text= f'Found {str(len(self.parts))} parts')

                self.style = ttk.Style()
                self.style.configure(
                    'PartFrame.TFrame',
                    background=self.style.lookup('TFrame', 'background'),
                    foreground='white',
                    borderwidth=0,
                    padding=10,
                )

                self.cf = CollapsingFrame(self.scrolled_frame)
                self.cf.pack(fill=BOTH, expand=True, padx=(5, 20))

                # time.sleep(1)

                for part in self.parts:
                    part_frame = ttk.Frame(self.cf, style='PartFrame.TFrame')
                    ttk.Button(
                        part_frame,
                        text="MODIFY",
                        command=lambda p=part: self.open_dialog(p),
                        bootstyle=INFO
                    ).pack(side=RIGHT, padx=(5, 0))
                    ttk.Button(
                        part_frame,
                        text="DELETE",
                        command=lambda p=part: self.delete_dialog(p['id']),
                        bootstyle=DANGER
                    ).pack(side=RIGHT, padx=(0, 5))

                    # style = ttk.Style()
                    # style.configure("TButton", font=('Segoe UI', 20))
                    
                    self.cf.add(child=part_frame, title=f"{part['name']}\n{part['std']} {part['unit']}\nTolerance: {part['hysteresis']:.2f} {part['unit']}")
            else:
                self.notificatiion("Get Parts", response['message'], False)
        except Exception as e:
            self.notificatiion("Get Parts", f"An error occurred: {e}", False)
    
    def validate_numeric_input(self, P):
        """Validate input to allow only numeric values."""
        if P == "" or P.replace('.', '', 1).isdigit():  # Allow empty input or numeric input
            return True
        return False

    def handle_get_stable_weight(self):
        try:
            response = self.get_stable_weight()
            if response['status'] == 200:
                self.part_std_entry.delete(0, tk.END)
                self.part_std_entry.insert(0, f"{int(response['data'])}")
                self.notificatiion("Get Stable Weight", response['message'], True)
            else:
                self.notificatiion("Get Stable Weight", response['message'], False)
        except Exception as e:
            self.notificatiion("Get Stable Weight", f"An error occurred: {e}", False)

    def handle_submit(self, name, std, unit, hysteresis, dialog, part=None):
        try:
            if part:
                response = self.update_part(part['id'], name, std, unit, hysteresis)
                if response['status'] == 200:
                    self.notificatiion("Update Part", response['message'], True)
                else:
                    self.notificatiion("Update Part", response['message'], False)
            else:
                response = self.create_part(name, std, unit, hysteresis)
                if response['status'] == 200:
                    self.notificatiion("Create Part", response['message'], True)
                else:
                    self.notificatiion("Create Part", response['message'], False)
        except Exception as e:
            self.notificatiion("Create/Update Part", f"An error occurred: {e}", False)
        finally:
            dialog.destroy()
            self.handle_get_parts()

    def handle_delete(self, part_id, dialog):
        try:
            response = self.delete_part(part_id)
            if response and response['status'] == 200:
                self.notificatiion("Delete Part", response['message'], True)
                self.handle_get_parts()
            else:
                self.notificatiion("Delete Part", response['message'], False)
        except Exception as e:
            self.notificatiion("Delete Part", f"An error occurred: {e}", False)
        finally:
            dialog.destroy()

    def open_dialog(self, part=None):
        dialog = tk.Toplevel(self, width=400)

        dialog.transient(self)
        dialog.grab_set()
        dialog.attributes("-topmost", True)

        ttk.Label(dialog, text="Part Name").pack(padx=20, pady=(10, 0), side=TOP, fill=X, anchor=W)
        part_name_entry = ttk.Entry(dialog)
        part_name_entry.pack(padx=20, pady=10, side=TOP, fill=X, anchor=W)

        numeric_vcmd = (self.register(self.validate_numeric_input), '%P')

        ttk.Label(dialog, text="Standard Weight").pack(padx=20, pady=(10, 0), side=TOP, fill=X, anchor=W)
        
        part_std_frame = ttk.Frame(dialog)
        part_std_frame.pack(padx=20, pady=10, side=TOP, fill=tk.X)
        self.part_std_entry = ttk.Entry(part_std_frame, validate='key', validatecommand=numeric_vcmd, justify=RIGHT)
        self.part_std_entry.pack(side=LEFT, fill=X, anchor=W)

        ttk.Button(
            part_std_frame,
            text="Get weight (gr)",
            command=lambda: self.handle_get_stable_weight(),
        ).pack(side=RIGHT)

        ttk.Label(dialog, text="Unit").pack(padx=20, pady=(10, 5), side=TOP, fill=X, anchor=W)
        unit_var = tk.StringVar(value='gr')
        ttk.Radiobutton(dialog, text='gr', variable=unit_var, value='gr').pack(padx=20, pady=5, side=TOP, fill=X, anchor=W)
        ttk.Radiobutton(dialog, text='kg', variable=unit_var, value='kg').pack(padx=20, pady=5, side=TOP, fill=X, anchor=W)

        ttk.Label(dialog, text="Tolerance").pack(padx=20, pady=(10, 0), side=TOP, fill=X, anchor=W)
        part_hysteresis_entry = ttk.Entry(dialog, validate='key', validatecommand=numeric_vcmd, justify=RIGHT)
        part_hysteresis_entry.pack(padx=20, pady=10, side=TOP, fill=X, anchor=W)

        if part:
            dialog.title("Modify Part")
            part_name_entry.insert(0, part['name'])
            self.part_std_entry.insert(0, part['std'] if part['unit'] == 'gr' else part['std'] * 1000)
            unit_var.set(part['unit'])
            part_hysteresis_entry.insert(0, part['hysteresis'])
        else:
            dialog.title("Create Part")

        action_frame = ttk.Frame(dialog)
        action_frame.pack(padx=20, pady=10, side=BOTTOM, fill=tk.X)
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=1)

        ttk.Button(
            action_frame,
            text="SUBMIT",
            bootstyle=SUCCESS,
            command=lambda: self.handle_submit(
                part_name_entry.get(),
                int(self.part_std_entry.get()) if unit_var.get() == 'gr' else float(self.part_std_entry.get()) / 1000,
                unit_var.get(),
                part_hysteresis_entry.get(),
                dialog,
                part
            )
        ).grid(row=0, column=0, sticky=NSEW, padx=(0, 5))

        ttk.Button(
            action_frame,
            text="CANCEL",
            bootstyle=SECONDARY,
            command=lambda: dialog.destroy()
        ).grid(row=0, column=1, sticky=NSEW, padx=(5, 0))

    def delete_dialog(self, part_id):
        dialog = tk.Toplevel(self)
        dialog.title("Confirm Delete")

        dialog.transient(self)
        dialog.grab_set()
        dialog.attributes("-topmost", True)

        ttk.Label(
            dialog, 
            text="Are you sure you want to delete\nthis part?",
            font=('Segoe UI', 20)
        ).pack(padx=20, pady=10)

        action_frame = ttk.Frame(dialog)
        action_frame.pack(padx=20, pady=10, side=BOTTOM, fill=tk.X)
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=1)

        ttk.Button(
            action_frame,
            text="DELETE",
            bootstyle=DANGER,
            command=lambda: self.handle_delete(part_id, dialog)
        ).grid(row=0, column=0, sticky=NSEW, padx=(0, 5))

        ttk.Button(
            action_frame,
            text="CANCEL",
            bootstyle=SECONDARY,
            command=dialog.destroy
        ).grid(row=0, column=1, sticky=NSEW, padx=(5, 0))
