import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.toast import ToastNotification
from ttkbootstrap.tableview import Tableview, TableColumn
from ttkbootstrap.style import Style
import tkinter as tk
import json
import os
from globalvar import GlobalConfig
import serial
import serial.tools.list_ports

class SummaryFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)

        self.log = tk.StringVar()

        self.popups = {
            "com": None,
            "log": None
        }
        
        GlobalConfig.select_com_options = GlobalConfig.get_available_com_ports()

        self.select_log_options = []

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
            text="Summary", 
            font=('Segoe UI', 42)
        ).grid(row=0,column=0, columnspan=2, sticky=NSEW, padx=5, pady=(10, 20))

        self.status_logs_label = ttk.Label(self, text="Found 0 logs", font=('Segoe UI', 24))
        self.status_logs_label.grid(row=1, column=0, columnspan=2, sticky=NSEW, padx=20)

        self.select_log_combobox = ttk.Menubutton(
            master=self,
            text='Select Log',
            bootstyle=SECONDARY,
            state=READONLY,
        )
        self.select_log_combobox.grid(row=2, column=0, columnspan=2, sticky=NSEW, ipady=10, padx=20, pady=5)
        self.select_log_combobox.bind('<Button-1>', lambda event: self.toggle_popup("log", self.select_log_combobox, self.select_log_options, self.log))
        self.create_popup(self.select_log_combobox, "log", self.select_log_options, self.log)

        self.export_button = ttk.Button(
            master=self,
            image='arrow-circle-down-36',
            text='Export',
            bootstyle=INFO,
            state=NORMAL,
        )
        self.export_button.grid(row=3, column=0, columnspan=2, sticky=NSEW, ipady=10, padx=20, pady=5)

        self.export_all_button = ttk.Button(
            master=self,
            image='downloading-36',
            text='Export All',
            bootstyle=INFO,
            state=NORMAL,
            command=lambda: self.export(self.select_log_options)
        )
        self.export_all_button.grid(row=4, column=0, columnspan=2, sticky=NSEW, ipady=10, padx=20, pady=5)
        
        # scrolled_frame = ScrolledFrame(self)
        # scrolled_frame.grid(row=3, column=0, columnspan=4, sticky=NSEW)

        self.log_frame = ttk.Frame(self)
        self.log_frame.grid(row=5, column=0, columnspan=6, sticky=NSEW)
        self.log_frame.grid_rowconfigure(0, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        self.handle_get_logs()

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

        if widget.cget("text").split('-')[0] == "log":
            self.export_button.config(state=NORMAL)
            self.display_table(widget.cget("text"))
            filenames = []
            filenames.append(widget.cget("text"))
            self.export_button.config(command=lambda:self.export(filenames))

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

    def handle_get_logs(self):
        self.select_log_options = []
        if os.path.exists("logs"):
            for filename in os.listdir("logs"):
                if filename.startswith("log-") and filename.endswith(".json"):
                    self.select_log_options.append(filename.split('.')[0])
                    
            self.select_log_options.sort(reverse=True)
            self.status_logs_label.config(text=f'Found {len(self.select_log_options)} logs')
            self.create_popup(self.select_log_combobox, "log", self.select_log_options, self.log)

            if len(self.select_log_options) > 0:
                self.export_all_button.config(state=NORMAL)

    def display_table(self, filename):
        for widget in self.log_frame.winfo_children():
            widget.destroy()

        log_file_path = os.path.join("logs", f'{filename}.json')
        if not os.path.isfile(log_file_path):
            print(f"Log file {log_file_path} does not exist.")
            return
        
        with open(log_file_path, 'r') as log_file:
            data = json.load(log_file)

        # Group data by part and count the occurrences of status "OK"
        grouped_data = {}
        for entry in data:
            part = entry['part']
            std = entry['std']
            unit = entry['unit']
            hysteresis = entry['hysteresis']
            status = entry['status']

            if part not in grouped_data:
                grouped_data[part] = {
                    'std': std,
                    'unit': unit,
                    'hysteresis': hysteresis,
                    'ok': 0,
                    'ng': 0
                }

            if status == "OK":
                grouped_data[part]['ok'] += 1
            else:
                grouped_data[part]['ng'] += 1

        rowdata = []
        for part, values in grouped_data.items():
            rowdata.append((
                part,
                values['std'],
                values['unit'],
                f"{values['hysteresis']:.2f}",
                values['ok'], 
                values['ng'],
            ))
        
        coldata = [
            {'text': 'Part', 'stretch': True},
            {'text': 'Standard', 'width': 150},
            {'text': 'Unit', 'width': 100},
            {'text': 'Tolerance', 'width': 150},
            {'text': 'OK', 'width': 150},
            {'text': 'NG', 'width': 150}
        ]
        table = Tableview(self.log_frame, coldata=coldata, rowdata=rowdata)
        table.grid(row=0, column=0, sticky=NSEW, padx=(20, 0), pady=(5, 0))
        table.align_heading_center(cid=table.get_column(2).cid)
        table.align_heading_right(cid=table.get_column(3).cid)
        table.align_column_center(cid=table.get_column(2).cid)
        table.align_column_right(cid=table.get_column(3).cid)
        style = Style()
        style.configure("Table.Treeview", font=('Segoe UI', 20), rowheight=40)
        style.configure("Table.Treeview.Heading", font=('Segoe UI', 20))

    def export(self, filenames):
        export_data = []

        for filename in filenames:
            log_file_path = os.path.join("logs", f'{filename}.json')
            if not os.path.isfile(log_file_path):
                print(f"Log file {log_file_path} does not exist.")
                return
            
            with open(log_file_path, 'r') as log_file:
                data = json.load(log_file)

                for entry in data:
                    export_data.append((
                        entry['date'],
                        entry['time'],
                        entry['part'],
                        entry['std'],
                        entry['unit'],
                        entry['measured'],
                        f"{entry['hysteresis']:.2f}",
                        entry['status']
                    ))

            columns = ['Date', 'Time', 'Part', 'Standard', 'Unit', 'Tolerance', 'Measured', 'Status']
        Tableview(None, coldata=columns, rowdata=export_data, delimiter=',').export_all_records()

    