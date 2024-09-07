import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.toast import ToastNotification
import tkinter as tk
from globalvar import GlobalConfig
import serial
import serial.tools.list_ports

class CalibrationFrame(ttk.Frame):
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
        self.grid_rowconfigure(5, weight=1)
        self.grid_columnconfigure(0, weight=1, minsize=100)
        self.grid_columnconfigure(1, weight=1, minsize=100)
        self.grid_columnconfigure(2, weight=1, minsize=100)
        self.grid_columnconfigure(3, weight=1, minsize=100)
        self.grid_columnconfigure(4, weight=1, minsize=100)
        self.grid_columnconfigure(5, weight=1, minsize=100)

        ttk.Label(
            self, 
            text="Calibration", 
            font=('Segoe UI', 42)
        ).grid(row=0, column=0, columnspan=2, sticky=NSEW, padx=5, pady=(10, 20))

        ttk.Label(
            self, 
            text="Current Calibration Factor", 
            font=('Segoe UI', 24)
        ).grid(row=1, column=0, columnspan=2, sticky=NSEW, padx=20)

        self.status_calfactor_label = ttk.Label(self, text="0", font=('Segoe UI', 36))
        self.status_calfactor_label.grid(row=2, column=0, columnspan=2, sticky=NSEW, padx=20)

        self.reset_button = ttk.Button(
            master=self,
            image='reset-36',
            text='Reset Calibration',
            bootstyle=SUCCESS,
            state=NORMAL,
            command=self.handle_reset_calibration
        )
        self.reset_button.grid(row=3, column=0, columnspan=2, sticky=NSEW, ipady=10, padx=20, pady=(10, 5))

        self.calibration_button = ttk.Button(
            master=self,
            image='play-circle-36',
            text='Start Calibration',
            bootstyle=INFO,
            state=NORMAL,
            command=self.handle_init_calibration
        )
        self.calibration_button.grid(row=4, column=0, columnspan=2, sticky=NSEW, ipady=10, padx=20, pady=5)
        
        scrolled_frame = ScrolledFrame(self)
        scrolled_frame.grid(row=5, column=0, columnspan=6, sticky=NSEW)

        self.log_frame = ttk.Frame(scrolled_frame)
        self.log_frame.pack(fill=BOTH, expand=True, padx=(5, 20))

        self.handle_get_calibration_factor()

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
    
    def notificatiion(self, title, message, status):
        toast = ToastNotification(
            title=title,
            message=message,
            duration=1500,
            bootstyle=SUCCESS if status else DANGER,
            position=(self.winfo_rootx(), self.winfo_rooty(), NW)
        )
        toast.show_toast()

    def init_calibration(self):
        if GlobalConfig.serial_connection and GlobalConfig.serial_connection.is_open:
            request = {
                "cmd": 10
            }
            if GlobalConfig.send_request(request):
                str_response = GlobalConfig.read_response()
                if str_response:
                    return GlobalConfig.parse_json(str_response)
        else:
            print("Serial connection is not open.")
        return None

    def get_calibration_factor(self):
        request = {
            "cmd": 13
        }
        if GlobalConfig.send_request(request):
            str_response = GlobalConfig.read_response()
            if str_response:
                return GlobalConfig.parse_json(str_response)
        return None

    def create_calibration_factor(self, known_weight):
        request = {
            "cmd": 11,
            "data": {
                "knownWeight": float(known_weight)
            }
        }
        if GlobalConfig.send_request(request):
            str_response = GlobalConfig.read_response()
            if str_response:
                return GlobalConfig.parse_json(str_response)
        return None

    def handle_get_calibration_factor(self):
        try:
            response = self.get_calibration_factor()
            if response['status'] == 200:
                self.notificatiion("Get Calibration Factor", response['message'], True)
                self.status_calfactor_label.config(text=f"{response['data']:.2f}")
            else:
                self.notificatiion("Get Calibration Factor", response['message'], False)
        except Exception as e:
            self.notificatiion("Get Calibration Factor", f"An error occurred: {e}", False)

    def handle_init_calibration(self):
        for widget in self.log_frame.winfo_children():
            widget.destroy()

        # Display initialization instructions on log_frame
        self.log_label = ttk.Label(
            self.log_frame, 
            anchor=W, 
            justify=LEFT, 
            text="Initialize calibration.",
            font=('Segoe UI', 18)
        )
        self.log_label.pack(fill=X, padx=20)

        self.log_label = ttk.Label(
            self.log_frame, 
            anchor=W, 
            justify=LEFT, 
            text="Place the load cell on a level stable surface.",
            font=('Segoe UI', 18)
        )
        self.log_label.pack(fill=X, padx=20)

        self.log_label = ttk.Label(
            self.log_frame, 
            anchor=W, 
            justify=LEFT, 
            text="Remove any load applied to the load cell.",
            font=('Segoe UI', 18)
        )
        self.log_label.pack(fill=X, padx=20)

        self.dot_text = ttk.Label(
            self.log_frame, 
            anchor=W, 
            justify=LEFT, 
            text="",
            font=('Segoe UI', 18)
        )
        self.dot_text.pack(fill=X, padx=20)

        # Start appending dots synchronously
        for _ in range(10):
            current_text =  self.dot_text.cget('text')
            self.dot_text.config(text=current_text + '.')
            self.update()  # Update the frame to reflect changes
            self.after(500)  # Wait for 500 milliseconds

        try:
            response = self.init_calibration()
            if response and response['status'] == 200:
                self.notificatiion("Initialize Calibration", response['message'], True)

                self.log_label = ttk.Label(
                    self.log_frame, 
                    anchor=W, 
                    justify=LEFT, 
                    text="Initialize complete.",
                    font=('Segoe UI', 18)
                )
                self.log_label.pack(fill=tk.X, padx=20)

                self.log_label = ttk.Label(
                    self.log_frame, 
                    anchor=W, 
                    justify=LEFT, 
                    text="Place **Known Weight** on the loadcell.",
                    font=('Segoe UI', 18)
                )
                self.log_label.pack(fill=tk.X, padx=20)

                self.dot_text = ttk.Label(
                    self.log_frame, 
                    anchor=W, 
                    justify=LEFT, 
                    text="",
                    font=('Segoe UI', 18)
                )
                self.dot_text.pack(fill=tk.X, padx=20)
                
                # Start appending dots synchronously
                for _ in range(10):
                    current_text =  self.dot_text.cget('text')
                    self.dot_text.config(text=current_text + '.')
                    self.update()  # Update the frame to reflect changes
                    self.after(500)  # Wait for 500 milliseconds

                self.open_dialog()
            else:
                self.notificatiion("Initialize Calibration", response['message'], False)
        except Exception as e:
            self.notificatiion("Initialize Calibration", f"An error occurred: {e}", False)

    def reset_calibration(self):
        request = {
            "cmd": 14
        }
        if GlobalConfig.send_request(request):
            str_response = GlobalConfig.read_response()
            if str_response:
                return GlobalConfig.parse_json(str_response)
        return None
    
    def handle_reset_calibration(self):
        try:    
            response = self.reset_calibration()
            if response['status'] == 200:
                self.log_label = tk.Label(self.log_frame, anchor=W, justify=LEFT, text=f"New calibration factor has been set to: {response['data']}")
                self.log_label.pack(fill=tk.X)

                self.log_label = tk.Label(self.log_frame, anchor=W, justify=LEFT, text="Reset Calibation complete.")
                self.log_label.pack(fill=tk.X)
                
                self.notificatiion("Reset Calibration Factor", response['message'], True)

                self.handle_get_calibration_factor()
            else:
                self.notificatiion("Reset Calibration Factor", response['message'], False)
        except Exception as e:
            self.notificatiion("Reset Calibration Factor", f"An error occurred: {e}", False)

    def open_dialog(self, part=None):
        dialog = tk.Toplevel(self, width=400)

        dialog.transient(self)
        dialog.grab_set()
        dialog.attributes("-topmost", True)

        numeric_vcmd = (self.register(self.validate_numeric_input), '%P')

        ttk.Label(dialog, text="Known Weight").pack(padx=20, pady=(10, 0), side=TOP, fill=X, anchor=W)
        
        known_weight_frame = ttk.Frame(dialog)
        known_weight_frame.pack(padx=20, pady=10, side=TOP, fill=tk.X)
        self.known_weight_entry = ttk.Entry(known_weight_frame, validate='key', validatecommand=numeric_vcmd, justify=RIGHT)
        self.known_weight_entry.pack(side=LEFT, fill=X, anchor=W)

        ttk.Label(
            known_weight_frame,
            text="gr",
            bootstyle=(SECONDARY, INVERSE),
            padding=(10, 0)
        ).pack(side=RIGHT, fill=Y)

        action_frame = ttk.Frame(dialog)
        action_frame.pack(padx=20, pady=10, side=BOTTOM, fill=tk.X)
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=1)

        ttk.Button(
            action_frame,
            text="SUBMIT",
            bootstyle=SUCCESS,
            command=lambda: self.handle_submit(self.known_weight_entry.get(), dialog)
        ).pack(padx=10, pady=10, side=LEFT, fill=tk.X)

        ttk.Button(
            action_frame,
            text="CANCEL",
            bootstyle=SECONDARY,
            command=lambda: dialog.destroy()
        ).pack(padx=10, pady=10, side=RIGHT, fill=tk.X)

    def handle_submit(self, known_weight, dialog):
        try:    
            response = self.create_calibration_factor(known_weight)
            if response['status'] == 200:
                self.log_label = ttk.Label(
                    self.log_frame, 
                    anchor=W, 
                    justify=LEFT, 
                    text=f"New calibration factor has been set to: {response['data']}",
                    font=('Segoe UI', 18)
                )
                self.log_label.pack(fill=tk.X, padx=20)

                self.log_label = ttk.Label(
                    self.log_frame, 
                    anchor=W, 
                    justify=LEFT, 
                    text="Calibation complete.",
                    font=('Segoe UI', 18)
                )
                self.log_label.pack(fill=tk.X, padx=20)
                
                self.notificatiion("Create Calibration Factor", response['message'], True)

                self.handle_get_calibration_factor()
            else:
                self.notificatiion("Create Calibration Factor", response['message'], False)
        except Exception as e:
            self.notificatiion("Create Calibration Factor", f"An error occurred: {e}", False)
        finally:
            dialog.destroy()

    def validate_numeric_input(self, P):
        """Validate input to allow only numeric values."""
        if P == "" or P.replace('.', '', 1).isdigit():  # Allow empty input or numeric input
            return True
        return False

