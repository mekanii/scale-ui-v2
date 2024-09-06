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
import cups
from globalvar import GlobalConfig
from collapsingframe import CollapsingFrame

class PrinterFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)
        
        GlobalConfig.select_com_options = GlobalConfig.get_available_com_ports()

        self.printers = []

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
            text="Printer Settings", 
            font=('Segoe UI', 42)
        ).grid(row=0, column=0, columnspan=2, sticky=NSEW, padx=5, pady=(10, 20))
        
        self.status_count_label = ttk.Label(self, text="Found 0 printers", font=('Segoe UI', 24))
        self.status_count_label.grid(row=3, column=0, columnspan=2, sticky=NSEW, padx=20, pady=(0, 5))

        self.scrolled_frame = ScrolledFrame(self)
        self.scrolled_frame.grid(row=4, column=0, columnspan=7, sticky=NSEW)

        # self.open_dialog()

        self.handle_get_printers()
    
    def get_printers(self):
        # Connect to the CUPS server
        conn = cups.Connection()

        # Get a list of printers
        printers = conn.getPrinters()

        # Get the default printer
        default_printer = conn.getDefault()

        printer_details = []

        for printer_name, printer_info in printers.items():
            # Get printer attributes
            attributes = conn.getPrinterAttributes(printer_name)

            # Extract relevant details
            # paper_sizes = attributes.get('media-supported', [])
            default_paper_size = attributes.get('media-default', 'Unknown')
            color_supported = attributes.get('color-supported', False)
            default_orientation = attributes.get('orientation-requested-default', 'Unknown')

            default_orientation = attributes.get('orientation-requested-default', 'Unknown')

            printer_details.append({
                'name': printer_name,
                'description': printer_info['printer-info'],
                'location': printer_info.get('printer-location', 'Unknown'),
                'default_paper_size': default_paper_size,
                'color_supported': color_supported,
                'default_orientation': default_orientation,
                'is_default': (printer_name == default_printer)
            })

        return printer_details

    def set_default_printer(self, printer_name):
        try:
            # Connect to the CUPS server
            conn = cups.Connection()
            # Set the specified printer as the default printer
            conn.setDefault(printer_name)
            self.notificatiion("Default Printer Set", f"Printer '{printer_name}' has been set as the default printer.", True)
        except Exception as e:
            self.notificatiion("Default Printer Set", f"An error occurred while setting the default printer: {e}", False)

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

    def notificatiion(self, title, message, status):
        toast = ToastNotification(
            title=title,
            message=message,
            duration=1500,
            bootstyle=SUCCESS if status else DANGER,
            position=(self.winfo_rootx(), self.winfo_rooty(), NW)
        )
        toast.show_toast()

    def handle_get_printers(self):
        try:
            printers = self.get_printers()
            
                
            for child in self.scrolled_frame.winfo_children():
                child.destroy()
            
            self.status_count_label.config(text= f'Found {str(len(printers))} printers')

            self.style = ttk.Style()
            self.style.configure(
                'PrinterFrame.TFrame',
                background=self.style.lookup('TFrame', 'background'),
                foreground='white',
                borderwidth=0,
                padding=10,
            )

            self.cf = CollapsingFrame(self.scrolled_frame)
            self.cf.pack(fill=BOTH, expand=True, padx=(5, 20))

            # time.sleep(1)

            for printer in printers:
                printer_frame = ttk.Frame(self.cf, style='PrinterFrame.TFrame')
                ttk.Button(
                    printer_frame, 
                    text="DEFAULT", 
                    command=lambda p=printer: self.set_default_printer(p['name']),
                    bootstyle=INFO,
                    state=DISABLED if printer['is_default'] else NORMAL
                ).pack(side=RIGHT, padx=(5, 0))

                # style = ttk.Style()
                # style.configure("TButton", font=('Segoe UI', 20))

                self.cf.add(
                    child=printer_frame,
                    title=f"{printer['description']}\n{printer['location']}\n{printer['default_paper_size']}"
                )
        except Exception as e:
            self.notificatiion("Get Printers", f"An error occurred: {e}", False)
    
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

        ttk.Button(
            dialog,
            text="SUBMIT",
            command=lambda: self.handle_submit(
                part_name_entry.get(),
                int(self.part_std_entry.get()) if unit_var.get() == 'gr' else float(self.part_std_entry.get()) / 1000,
                unit_var.get(),
                part_hysteresis_entry.get(),
                dialog,
                part
            )
        ).pack(padx=10, pady=10, side=LEFT, fill=tk.X)

        ttk.Button(
            dialog,
            text="CANCEL",
            command=lambda: dialog.destroy()
        ).pack(padx=10, pady=10, side=RIGHT, fill=tk.X)

