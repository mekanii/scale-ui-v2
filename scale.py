from pathlib import Path
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
import threading
import queue
import cups
from globalvar import GlobalConfig

class ScaleFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)

        pygame.mixer.init()

        self.current_date = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.last_part = tk.StringVar()
        self.part = tk.StringVar()
        self.part_std = tk.StringVar()
        self.hysteresis = tk.StringVar()
        self.weight = tk.DoubleVar(value=0.00)
        self.scale = tk.StringVar()
        self.last_check = tk.IntVar(value=0)
        self.count_pack = tk.StringVar()
        self.count_ok = tk.StringVar()
        self.count_ng = tk.StringVar()
        self.count_ok_setpoint = tk.IntVar(value=0)

        self.flag_tare = tk.BooleanVar(value=False)
        self.flag_pause = tk.BooleanVar(value=False)

        self.count_try = tk.IntVar(value=0)

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
        self.grid_rowconfigure(6, weight=0)
        # self.grid_rowconfigure(7, weight=0)
        self.grid_columnconfigure(0, weight=1, minsize=100)
        self.grid_columnconfigure(1, weight=1, minsize=100)
        self.grid_columnconfigure(2, weight=1, minsize=100)
        self.grid_columnconfigure(3, weight=1, minsize=100)
        self.grid_columnconfigure(4, weight=1, minsize=100)
        self.grid_columnconfigure(5, weight=1, minsize=100)

        ttk.Label(
            self, 
            text="Scale", 
            font=('Segoe UI', 42)
        ).grid(row=0, column=0, columnspan=2, sticky=NSEW, padx=5, pady=(10, 20))

        self.status_parts_label = ttk.Label(self, text="Found 0 parts", font=('Segoe UI', 24))
        self.status_parts_label.grid(row=1, column=0, columnspan=2, sticky=NSEW, padx=20)

        self.select_part_combobox = ttk.Menubutton(
            master=self,
            text="Select Part",
            bootstyle=SECONDARY,
            state=READONLY,
        )
        self.select_part_combobox.grid(row=2, column=0, columnspan=2, sticky=NSEW, ipady=10, padx=20, pady=5)
        self.select_part_combobox.bind('<Button-1>', lambda event: self.toggle_popup("part", self.select_part_combobox, self.select_part_options, self.part))
        self.create_popup(self.select_part_combobox, "part", self.select_part_options, self.part)

        self.reload_button = ttk.Button(
            master=self,
            image='sync-36',
            text='Reload',
            style='Info.TButton',
            command=self.handle_get_parts
        )
        self.reload_button.grid(row=3, column=0, columnspan=2, sticky=NSEW, ipady=10, padx=20, pady=5)

        self.tare_button = ttk.Button(
            master=self,
            image='reset-36',
            text='Tare',
            style='Info.TButton',
            command=self.handle_tare
        )
        self.tare_button.grid(row=4, column=0, columnspan=2, sticky=NSEW, ipady=10, padx=20, pady=5)

        # self.std_label = ttk.Label(self, textvariable=self.std, justify=RIGHT, anchor=E, font=('Segoe UI', 24))
        # self.std_label.grid(row=5, column=0, columnspan=6, sticky=NSEW, padx=15, pady=(15,5))
        
        self.weight_label = ttk.Label(self, textvariable=self.scale, justify=RIGHT, anchor=E, font=('Segoe UI', 200))
        self.weight_label.grid(row=5, column=0, columnspan=6, sticky=NSEW, padx=15, pady=5)

        self.check_label = ttk.Label(self, justify=RIGHT, anchor=E, font=('Arial', 56))
        self.check_label.grid(row=6, column=0, columnspan=6, sticky=NSEW, padx=15, pady=5)

        status_label_frame = ttk.Frame(self)
        status_label_frame.grid(row=0, column=2, rowspan=5, columnspan=4, sticky=NSEW, padx=5, pady=5)
        status_label_frame.grid_rowconfigure(0, weight=0)
        status_label_frame.grid_rowconfigure(1, weight=0)
        status_label_frame.grid_rowconfigure(2, weight=0)
        status_label_frame.grid_rowconfigure(3, weight=0)
        status_label_frame.grid_rowconfigure(4, weight=0)
        status_label_frame.grid_rowconfigure(5, weight=0)
        status_label_frame.grid_columnconfigure(0, weight=1)

        status_date_label = ttk.Label(
            status_label_frame, 
            textvariable=self.current_date, 
            justify=RIGHT, 
            anchor=E, 
            font=('Segoe UI', 28)
        )
        status_date_label.grid(row=0, sticky=NE, padx=5, pady=(20,0))

        part_std_label = ttk.Label(
            status_label_frame, 
            textvariable=self.part_std, 
            justify=RIGHT, 
            anchor=E, 
            font=('Segoe UI', 28)
        )
        part_std_label.grid(row=1, sticky=NE, padx=5)

        hysteresis_label = ttk.Label(
            status_label_frame, 
            textvariable=self.hysteresis,
            justify=RIGHT, 
            anchor=E, 
            font=('Segoe UI', 28)
        )
        hysteresis_label.grid(row=2, sticky=NE, padx=5)

        self.status_count_label = ttk.Label(
            status_label_frame, 
            textvariable=self.count_pack, 
            justify=RIGHT, 
            anchor=E, 
            font=('Segoe UI', 72)
        )
        self.status_count_label.grid(row=3, sticky=NE, padx=5)

        self.status_count_label = ttk.Label(
            status_label_frame, 
            textvariable=self.count_ok,
            justify=RIGHT, 
            anchor=E, 
            font=('Segoe UI', 48)
        )
        self.status_count_label.grid(row=4, sticky=NE, padx=5)

        self.status_count_label = ttk.Label(
            status_label_frame, 
            textvariable=self.count_ng, 
            justify=RIGHT, 
            anchor=E, 
            font=('Segoe UI', 48)
        )
        self.status_count_label.grid(row=5, sticky=NE, padx=5)

        
        # status_label = ttk.Label(status_label_frame, text="Packages", justify=RIGHT, anchor=E, font=('Segoe UI', 18))
        # status_label.grid(row=1, sticky=SE, padx=15, pady=(0, 5))

        # self.update_com_ports()

        self.handle_get_parts()
        self.update_scale()
        

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

        # self.open_dialog()

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

                self.status_parts_label.config(text=f"Found {len(self.select_part_options)} parts")
                
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
        if self.flag_tare.get() == False and self.flag_pause.get() == False:
            try:
                if self.part.get() != "":
                    part = ast.literal_eval(self.part.get())

                    if self.last_part.get() != self.part.get():
                        self.handle_refresh_data_set()
                        self.last_part.set(self.part.get())
                        count, count_ok, count_ng = self.count_log_data(part['name'])

                        if (part['pack'] > 0):
                            qty_packed = self.sum_qty_by_part(part['name'])
                            count_ok_session = (count_ok - qty_packed) % part['pack']
                            
                        else:
                            count_ok_session = count_ok
                        
                        self.count_pack.set(f"{count}")
                        self.count_ok.set(f"[ {count_ok_session} / {part['pack']} ] {count_ok} OK")
                        self.count_ng.set(f"{count_ng} NG")
                        # self.std.set(f"Standard Weight: {part['std']} {part['unit']}, Tolerance: {part['hysteresis']:.2f}")
                        self.part_std.set(f"Standard Weight: {part['std']} {part['unit']}")
                        self.hysteresis.set(f"Tolerance: {part['hysteresis']:.2f}")

                    
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

                            self.log_data(part, float(format(weight, '.2f')) if part['unit'] == 'kg' else int(weight), "OK")
                            count, count_ok, count_ng = self.count_log_data(part['name'])
                            
                            if (part['pack'] > 0):
                                qty_packed = self.sum_qty_by_part(part['name'])
                                count_ok_session = (count_ok - qty_packed) % part['pack']
                                if count_ok_session == 0:
                                    result_queue = queue.Queue()
                                    self.count_try.set(0)
                                    threading.Thread(target=self.run_print_label, args=(part, part['pack'], result_queue)).start()
                                    self.after(100, self.check_print_label_result, result_queue)
                                    # GlobalConfig.print_label(part, self.count_ok_setpoint.get())
                            else:
                                count_ok_session = count_ok
                            
                            self.count_pack.set(f"{count}")
                            self.count_ok.set(f"[ {count_ok_session} / {part['pack']} ] {count_ok} OK")
                            # self.count_ng.set(f"{count_ng} NG")

                        elif check == 2 and check != self.last_check.get():
                            self.play_tone("NG")
                            self.check_label.config(foreground='red')
                            self.check_label.config(text="NOT GOOD")

                            self.log_data(part, float(format(weight, '.2f')) if part['unit'] == 'kg' else int(weight), "NG")
                            count, count_ok, count_ng = self.count_log_data(part['name'])

                            self.count_pack.set(f"{count}")
                            # self.count_ok.set(f"[ {count_ok_session} / {self.count_ok_setpoint.get()} ] {count_ok} OK")
                            self.count_ng.set(f"{count_ng} NG")
                        elif check == 0 and check != self.last_check.get():
                            self.check_label.config(text="")
                        
                        self.last_check.set(check)
                        self.scale.set(scale)
                        self.weight_label.config(text=scale)
            except Exception as e:
                print(f"An error occurred: {e}")

        # Schedule the next update
        self.after(50, self.update_scale)  # Update every second

    def log_data(self, part, scale, status):
        # Get the current date in the format yyyy-mm-dd
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")
        log_filename = f"logs/log-{current_date}.json"

        # Check if the logs directory exists, if not, create it
        if not os.path.exists("logs"):
            os.makedirs("logs")

        # Check if the log file exists
        if not os.path.isfile(log_filename):
            # Create the log file with an empty list if it doesn't exist
            with open(log_filename, 'w') as log_file:
                json.dump([], log_file)

        # Prepare the log entry
        log_entry = {
            "date": current_date,
            "time": current_time,
            "part": part['name'],
            "std": part['std'],
            "unit": part['unit'],
            "hysteresis": part['hysteresis'],
            "measured": scale,
            "status": status
        }

        # Append the log entry to the existing log file
        with open(log_filename, 'r+') as log_file:
            # Load existing data
            data = json.load(log_file)
            # Append the new entry
            data.append(log_entry)
            # Move the cursor to the beginning of the file
            log_file.seek(0)
            # Write the updated data back to the file
            json.dump(data, log_file, indent=4)

    def count_log_data(self, part_name):
        # Get the current date in the format yyyy-mm-dd
        current_date = datetime.now().strftime("%Y-%m-%d")
        log_filename = f"logs/log-{current_date}.json"

        # Check if the log file exists
        if not os.path.isfile(log_filename):
            return 0, 0, 0  # Return 0 if the log file does not exist

        # Initialize count
        count = 0
        count_ok = 0
        count_ng = 0

        # Read the log file and count entries for the specified part
        with open(log_filename, 'r') as log_file:
            data = json.load(log_file)
            count = sum(1 for entry in data if entry['part'] == part_name)

            count_ok = sum(1 for entry in data if entry['part'] == part_name and entry['status'] == "OK")
            count_ng = sum(1 for entry in data if entry['part'] == part_name and entry['status'] == "NG")

        return count, count_ok, count_ng

    def sum_qty_by_part(self, part_name):
        # Get the current date in the format yyyy-mm-dd
        current_date = datetime.now().strftime("%Y-%m-%d")
        log_filename = f"logs/print-job-{current_date}.json"

        # Check if the log file exists
        if not os.path.isfile(log_filename):
            print(f"Log file {log_filename} does not exist.")
            return 0

        # Initialize a variable to store the sum of quantities for the selected part
        total_qty = 0

        # Read the log file and sum quantities for the selected part
        with open(log_filename, 'r') as log_file:
            data = json.load(log_file)
            for entry in data:
                if entry['part'] == part_name:
                    qty = entry.get('qty', 0)
                    total_qty += qty

        return total_qty

    def validate_numeric_input(self, P):
        """Validate input to allow only numeric values."""
        if P == "" or P.replace('.', '', 1).isdigit():  # Allow empty input or numeric input
            return True
        return False
    
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

    def open_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Set Point")
        dialog.geometry("400x200")

        dialog.transient(self)
        dialog.grab_set()
        dialog.attributes("-topmost", True)

        self.flag_pause.set(True)

        numeric_vcmd = (self.register(self.validate_numeric_input), '%P')

        ttk.Label(
            dialog, 
            text="Set Point",
            font=('Segoe UI', 20)
        ).pack(padx=20, pady=(10, 0), side=TOP, fill=X, anchor=W)

        set_point_entry = ttk.Entry(
            dialog,
            validate='key',
            validatecommand=numeric_vcmd,
            justify=RIGHT,
            font=('Segoe UI', 20)
        )
        set_point_entry.pack(padx=20, pady=10, side=TOP, fill=X, anchor=W)

        action_frame = ttk.Frame(dialog)
        action_frame.pack(padx=20, pady=10, side=BOTTOM, fill=tk.X)
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=1)

        ttk.Button(
            action_frame,
            text="SUBMIT",
            bootstyle=SUCCESS,
            command=lambda: self.handle_submit(
                set_point_entry.get(),
                dialog
            )
        ).grid(row=0, column=0, sticky=NSEW, padx=(0, 5))

        ttk.Button(
            action_frame,
            text="CANCEL",
            bootstyle=SECONDARY,
            command=lambda: self.handle_cancel(dialog)
        ).grid(row=0, column=1, sticky=NSEW, padx=(5, 0))

    def handle_submit(self, set_point, dialog):
        self.count_ok_setpoint.set(set_point)
        self.flag_pause.set(False)
        dialog.destroy()

    def handle_cancel(self, dialog):
        self.count_ok_setpoint.set(0)
        self.flag_pause.set(False)
        dialog.destroy()

    def run_print_label(self, part, count_ok_setpoint, result_queue):
        # Call the print_label function and put the result in the queue
        result = GlobalConfig.print_label(part, count_ok_setpoint)
        result_queue.put(result)

    def check_print_label_result(self, result_queue):
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
                command=lambda: self.cancel_last_print_job(self.dialog)
            )

        try:
            # Try to get the result from the queue
            result = result_queue.get_nowait()
            if result == True:
                self.dialog.destroy()
                self.flag_pause.set(False)
        except queue.Empty:
            # If the queue is empty, check again after a short delay
            current_try = self.count_try.get()
            self.count_try.set(current_try + 1)
            if self.count_try.get() == 200:
                self.cancel_button.pack(fill=X, side=BOTTOM, padx=30, pady=20)
            self.after(100, self.check_print_label_result, result_queue)

    def cancel_last_print_job(self, dialog):
        # Connect to the CUPS server
        conn = cups.Connection()

        printer_name = conn.getDefault()

        # Get the list of jobs for the specified printer
        jobs = conn.getJobs(which_jobs='all', my_jobs=True)

        if not jobs:
            print("No print jobs found.")
            return False

        # Find the last job (most recent job)
        last_job_id = max(jobs.keys())
        # last_job = jobs[last_job_id]

        # Cancel the last job
        conn.cancelJob(last_job_id)
        print(f"Canceled job ID {last_job_id} for printer {printer_name}.")
        
        dialog.destroy()