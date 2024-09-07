import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.toast import ToastNotification
from ttkbootstrap.tableview import Tableview, TableColumn
from ttkbootstrap.style import Style
import tkinter as tk
import serial
import serial.tools.list_ports
import json
import ast
import os
import pygame
import time
import cups
import threading
import queue
from globalvar import GlobalConfig
from collapsingframe import CollapsingFrame

class PrinterFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)
        
        GlobalConfig.select_com_options = GlobalConfig.get_available_com_ports()

        self.printers = []
        self.logs = []
        self.log = tk.StringVar(value='Select Log')
        self.text_button = tk.StringVar(value='Print Job')

        self.flag_pause = tk.BooleanVar(value=False)
        self.count_try = tk.IntVar(value=0)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1, minsize=100)
        self.grid_columnconfigure(1, weight=1, minsize=100)
        self.grid_columnconfigure(2, weight=1, minsize=100)
        self.grid_columnconfigure(3, weight=1, minsize=100)
        self.grid_columnconfigure(4, weight=1, minsize=100)
        self.grid_columnconfigure(5, weight=1, minsize=100)

        self.scrolled_frame = ScrolledFrame(self)
        self.scrolled_frame.grid(row=0, column=0, columnspan=6, sticky=NSEW)

        ttk.Label(
            self.scrolled_frame, 
            text="Printer Settings", 
            font=('Segoe UI', 42)
        ).pack(side=TOP, anchor=W, fill=X, padx=5, pady=(10, 20))
        # .grid(row=0, column=0, columnspan=2, sticky=NSEW, padx=5, pady=(10, 20))
        
        self.status_count_label = ttk.Label(self.scrolled_frame, text="Found 0 printers", font=('Segoe UI', 24))
        self.status_count_label.pack(side=TOP, anchor=W, fill=X, padx=20, pady=(0, 5))
        # self.status_count_label.grid(row=3, column=0, columnspan=2, sticky=NSEW, padx=20, pady=(0, 5))

        self.collapsing_frame = ttk.Frame(self.scrolled_frame)
        self.collapsing_frame.pack(side=TOP, fill=X, padx=20, pady=(0, 5))

        self.handle_get_printers()

        self.status_logs_label = ttk.Label(
            self.scrolled_frame, 
            text="Found 0 logs", 
            font=('Segoe UI', 24)
        )
        self.status_logs_label.pack(side=TOP, fill=X, padx=20, pady=(20, 0))

        control_frame = ttk.Frame(self.scrolled_frame)
        control_frame.pack(side=TOP, fill=X)
        control_frame.grid_rowconfigure(0, weight=0)
        control_frame.grid_columnconfigure(0, minsize=100, weight=1)
        control_frame.grid_columnconfigure(1, minsize=100, weight=1)
        control_frame.grid_columnconfigure(2, minsize=100, weight=1)

        self.select_log_combobox = ttk.Combobox(
            master=control_frame,
            values=self.logs,
            textvariable=self.log,
            state=READONLY,
            style='Secondary.TCombobox',
            font=('Segoe UI', 20)
        )
        # self.select_log_combobox.pack(side=TOP, anchor=W, padx=20, pady=5)
        self.select_log_combobox.grid(row=0, column=0, padx=20, pady=5, sticky=NSEW)
        self.select_log_combobox.grid_propagate(False)
        self.select_log_combobox.bind('<<ComboboxSelected>>', self.combobox_select)

        self.handle_get_logs()

        self.print_button = ttk.Button(
            control_frame,
            textvariable=self.text_button,
            bootstyle=INFO,
            state=DISABLED,
            # command=self.handle_print
        )
        # self.print_button.pack(side=TOP, anchor=W, padx=20, pady=5)
        self.print_button.grid(row=0, column=1, pady=5, sticky=NSEW)

        self.table_frame = ttk.Frame(self.scrolled_frame)
        self.table_frame.pack(side=TOP, fill=BOTH, expand=True, padx=20, pady=(5, 0))
        
    
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
            
                
            for child in self.collapsing_frame.winfo_children():
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
            self.cf.pack(side=TOP,fill=BOTH, expand=True, padx=(5, 20))

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
                    title=f"{printer['description']}\n{printer['location']}"
                )
        except Exception as e:
            self.notificatiion("Get Printers", f"An error occurred: {e}", False)
    
    def handle_get_logs(self):
        self.select_log_options = []
        if os.path.exists("logs"):
            for filename in os.listdir("logs"):
                if filename.startswith("print-job-") and filename.endswith(".json"):
                    self.select_log_options.append(f"    {filename.split('.')[0]}")
                    
            self.select_log_options.sort(reverse=True)
            self.logs = self.select_log_options
            self.select_log_combobox['values'] = self.logs

            self.status_logs_label.config(text=f'Found {len(self.logs)} logs')

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

    def combobox_select(self, event):
        self.log.set(event.widget.get().replace('    ', ''))
        self.display_table(self.log.get())

    def display_table(self, filename):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        log_file_path = os.path.join("logs", f'{filename}.json')
        if not os.path.isfile(log_file_path):
            print(f"Log file {log_file_path} does not exist.")
            return
        
        with open(log_file_path, 'r') as log_file:
            data = json.load(log_file)

        rowdata = []
        for entry in data:
            rowdata.append((
                entry['jobid'],
                entry['time'],
                entry['part'],
                entry['qty'],
                {
                    3: "PENDING",
                    4: "HELD",
                    5: "PROCESSING",
                    6: "STOPPED",
                    7: "CANCELED",
                    8: "ABORTED",
                    9: "COMPLETED"
                }[entry['state']]
            ))
        
        coldata = [
            {'text': 'Job ID', 'width': 100},
            {'text': 'Time', 'width': 150},
            {'text': 'Part', 'stretch': True},
            {'text': 'Qty', 'width': 100},
            {'text': 'State', 'width': 150},
        ]
        table = Tableview(
            self.table_frame,
            coldata=coldata,
            rowdata=rowdata,
            paginated=True,
        )
        table.pack(fill=BOTH, expand=True)
        table.view.bind("<<TreeviewSelect>>", self.on_table_select)

        # table.align_heading_center(cid=table.get_column(2).cid)
        # table.align_heading_right(cid=table.get_column(3).cid)
        # table.align_column_center(cid=table.get_column(2).cid)
        # table.align_column_right(cid=table.get_column(3).cid)
        style = Style()
        style.configure("Table.Treeview", font=('Segoe UI', 20), rowheight=40)
        style.configure("Table.Treeview.Heading", font=('Segoe UI', 20))

    def on_table_select(self, event):
        # Get the selected item
        selected_item = event.widget.selection()
        if selected_item:
            job_id = event.widget.item(selected_item)['values'][0]
            self.text_button.set(f'Print Job: {job_id}')
            self.print_button.config(state=NORMAL)
            self.print_button.config(command=lambda: self.handle_print(job_id))

    def handle_print(self, job_id):
        result_queue = queue.Queue()
        self.count_try.set(0)
        threading.Thread(target=self.run_print_label, args=(job_id, result_queue)).start()
        self.after(100, self.check_print_label_result, job_id, result_queue)

    def run_print_label(self, job_id, result_queue):
        result = GlobalConfig.reprint_job(job_id)
        result = result_queue.put(result)

    def check_print_label_result(self, job_id, result_queue):
        if self.flag_pause.get() == False:
            dialog_width = 400
            dialog_height = 200

            self.dialog = tk.Toplevel(self, width=dialog_width, height=dialog_height)

            parent_x = self.winfo_rootx()
            parent_y = self.winfo_rooty()
            parent_width = self.winfo_width()
            parent_height = self.winfo_height()

            center_x = parent_x + (parent_width // 2) - (dialog_width // 2)
            center_y = parent_y + (parent_height // 2) - (dialog_height // 2)

            self.dialog.geometry(f"{dialog_width}x{dialog_height}+{center_x}+{center_y}")

            self.dialog.transient(self)
            self.dialog.grab_set()
            self.dialog.attributes("-topmost", True)
            self.dialog.overrideredirect(True)

            self.flag_pause.set(True)

            # Add a label and a progress bar (spinner) to the dialog
            ttk.Label(
                self.dialog, 
                text="Printing, please wait...", 
                font=('Segoe UI', 20)
            ).pack(padx=30, pady=20)
            progress = ttk.Progressbar(self.dialog, mode='indeterminate')
            progress.pack(fill=X, padx=30, pady=20)
            progress.start()

            # action_frame = ttk.Frame(self.dialog)
            # action_frame.pack(padx=20, pady=10, side=BOTTOM, fill=tk.X)
            # action_frame.grid_columnconfigure(0, weight=1)
            # action_frame.grid_columnconfigure(1, weight=1)

            self.cancel_button = ttk.Button(
                self.dialog,
                text="CANCEL",
                bootstyle=DANGER,
                command=lambda: self.cancel_print_job(job_id, self.dialog)
            )

        try:
            # Try to get the result from the queue
            result = result_queue.get_nowait()
            if result == True:
                self.dialog.destroy()
                self.flag_pause.set(False)
                self.display_table(self.log.get())
        except queue.Empty:
            # If the queue is empty, check again after a short delay
            current_try = self.count_try.get()
            self.count_try.set(current_try + 1)
            if self.count_try.get() == 200:
                self.cancel_button.pack(fill=X, side=BOTTOM, padx=30, pady=20)
            self.after(100, self.check_print_label_result, job_id, result_queue)

    def cancel_print_job(self, job_id, dialog):
        # Connect to the CUPS server
        conn = cups.Connection()

        printer_name = conn.getDefault()

        # Get the list of jobs for the specified printer
        jobs = conn.getJobs(which_jobs='all', my_jobs=True)

        if not jobs:
            print("No print jobs found.")
            return False

        # Cancel the last job
        conn.cancelJob(job_id)
        print(f"Canceled job ID {job_id} for printer {printer_name}.")
        
        dialog.destroy()