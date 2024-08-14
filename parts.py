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
        self.grid_rowconfigure(3, weight=1)
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
            command=self.open_dialog
        )
        self.create_button.grid(row=2, column=3, sticky=NSEW, ipady=10, padx=5, pady=5)
        
        scrolled_frame = ScrolledFrame(self)
        scrolled_frame.grid(row=3, column=0, columnspan=4, sticky=NSEW)

        self.cf = CollapsingFrame(scrolled_frame)
        self.cf.pack(fill=BOTH, expand=True, padx=(5, 20))

        # self.open_dialog()

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

                self.style = ttk.Style()
                self.style.configure(
                    'PartFrame.TFrame',
                    background=self.style.lookup('TFrame', 'background'),
                    foreground='white',
                    borderwidth=0,
                    padding=10
                )

                for part in self.parts:
                    part_frame = ttk.Frame(self.cf, style='PartFrame.TFrame')
                    ttk.Button(part_frame, text="DELETE", command=lambda: self.delete_dialog(part['id'])).pack(side=RIGHT, padx=(5, 0))
                    ttk.Button(part_frame, text="MODIFY", command=lambda: self.open_dialog(part)).pack(side=RIGHT, padx=(0, 5))

                    
                    self.cf.add(child=part_frame, title=f"{part['name']}\n{part['std']} {part['unit']}")
            else:
                self.notificatiion("Get Parts", response['message'], False)
        except Exception as e:
            self.notificatiion("Get Parts", f"An error occurred: {e}", False)
    
    def validate_numeric_input(self, action, value_if_allowed, text):
        if action == '1':
            return text.isdigit() and int(value_if_allowed) > 0
        return True

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

    def handle_submit(self, name, std, unit, dialog, part=None):
        try:
            if part:
                response = self.update_part(part['id'], name, std, unit)
                if response['status'] == 200:
                    self.notificatiion("Update Part", response['message'], True)
                else:
                    self.notificatiion("Update Part", response['message'], False)
            else:
                response = self.create_part(name, std, unit)
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

        ttk.Label(dialog, text="Part Name:").pack(padx=20, pady=(10, 0), side=TOP, fill=X, anchor=W)
        part_name_entry = ttk.Entry(dialog)
        part_name_entry.pack(padx=20, pady=10, side=TOP, fill=X, anchor=W)

        numeric_vcmd = (self.register(self.validate_numeric_input), '%d', '%P', '%S')

        ttk.Label(dialog, text="Standard Weight:").pack(padx=20, pady=(10, 0), side=TOP, fill=X, anchor=W)
        
        part_std_frame = ttk.Frame(dialog)
        part_std_frame.pack(padx=20, pady=10, side=TOP, fill=tk.X)
        self.part_std_entry = ttk.Entry(part_std_frame, validate='key', validatecommand=numeric_vcmd, justify=RIGHT)
        self.part_std_entry.pack(side=LEFT, fill=X, anchor=W)

        ttk.Button(
            part_std_frame,
            text="Get weight (gr)",
            command=lambda: self.handle_get_stable_weight(),
        ).pack(side=RIGHT)

        ttk.Label(dialog, text="Unit:").pack(padx=20, pady=(10, 5), side=TOP, fill=X, anchor=W)
        unit_var = tk.StringVar(value='gr')
        ttk.Radiobutton(dialog, text='gr', variable=unit_var, value='gr').pack(padx=20, pady=5, side=TOP, fill=X, anchor=W)
        ttk.Radiobutton(dialog, text='kg', variable=unit_var, value='kg').pack(padx=20, pady=5, side=TOP, fill=X, anchor=W)

        if part:
            dialog.title("Modify Part")
            part_name_entry.insert(0, part['name'])
            self.part_std_entry.insert(0, part['std'] if part['unit'] == 'gr' else part['std'] * 1000)
            unit_var.set(part['unit'])
        else:
            dialog.title("Create Part")

        ttk.Button(
            dialog,
            text="SUBMIT",
            command=lambda: self.handle_submit(
                part_name_entry.get(),
                int(self.part_std_entry.get()) if unit_var.get() == 'gr' else float(self.part_std_entry.get()) / 1000,
                unit_var.get(),
                dialog,
                part
            )
        ).pack(padx=10, pady=10, side=LEFT, fill=tk.X)

        ttk.Button(
            dialog,
            text="CANCEL",
            command=lambda: dialog.destroy()
        ).pack(padx=10, pady=10, side=RIGHT, fill=tk.X)

    def delete_dialog(self, part_id):
        dialog = tk.Toplevel(self)
        dialog.title("Confirm Delete")

        ttk.Label(dialog, text="Are you sure you want to delete this part?").pack(padx=20, pady=10)

        ttk.Button(
            dialog,
            text="DELETE",
            bootstyle=DANGER,
            command=lambda: self.handle_delete(part_id, dialog)
        ).pack(side=LEFT, padx=10, pady=10)

        ttk.Button(
            dialog,
            text="CANCEL",
            command=dialog.destroy
        ).pack(side=RIGHT, padx=10, pady=10)
