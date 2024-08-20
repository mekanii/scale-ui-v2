from pathlib import Path
from PIL import Image
Image.CUBIC = Image.BICUBIC

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
import json
import ast

from scale import ScaleFrame
from parts import PartsFrame
from summary import SummaryFrame
from settings import SettingsFrame

PATH = Path(__file__).parent / 'assets'

class Main(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.pack(expand=True, fill=BOTH)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self.images = [
            ttk.PhotoImage(
                name='package-36',
                file=PATH / 'icons/package-36.png'),
            ttk.PhotoImage(
                name='device-36',
                file=PATH / 'icons/device-36.png'),
            ttk.PhotoImage(
                name='book-36',
                file=PATH / 'icons/book-36.png'),
            ttk.PhotoImage(
                name='cog-36',
                file=PATH / 'icons/cog-36.png')
        ]
        
        self.menu_selected = tk.StringVar(value='main')

        self.status_run = tk.BooleanVar(value=True)
        self.status_run_text = tk.StringVar(value='STOP')
        self.status_run_bootstyle = 'square-toggle-danger'

        self.com_port = tk.StringVar()
        self.part = tk.StringVar()

        self.serial_connection = None

        # menu buttons
        menu_frame = ttk.Frame(self, bootstyle=SECONDARY)
        menu_frame.grid(row=0, column=0, sticky=NS)

        menu_main_btn = ttk.Radiobutton(
            master=menu_frame,
            image='package-36',
            text='MAIN',
            value='main',
            variable=self.menu_selected,
            compound=TOP,
            bootstyle=TOOLBUTTON,
            command=lambda: self.show_scale()
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
            command=lambda: self.show_parts()
        )
        menu_parts_btn.pack(side=TOP, fill=BOTH, ipady=10)

        menu_parts_btn = ttk.Radiobutton(
            master=menu_frame,
            image='book-36',
            text='SUMMARY',
            value='summary',
            variable=self.menu_selected,
            compound=TOP,
            bootstyle=TOOLBUTTON,
            command=lambda: self.show_summary()
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
            command=lambda: self.show_settings()
        )
        menu_setting_btn.pack(side=TOP, fill=BOTH, ipady=10)

        self.content_frame = ttk.Frame(self)
        self.content_frame.grid(row=0, column=1, sticky=NSEW, padx=5, pady=5)
        self.content_frame.grid_rowconfigure(0, weight=1)  # Add this line
        self.content_frame.grid_columnconfigure(0, weight=1)

        # self.frame = None

        self.show_scale()

    def show_scale(self):
        self.clear_content()
        ScaleFrame(self.content_frame).tkraise()

    def show_parts(self):
        self.clear_content()
        PartsFrame(self.content_frame).tkraise()

    def show_summary(self):
        self.clear_content()
        SummaryFrame(self.content_frame).tkraise()

    def show_settings(self):
        self.clear_content()
        SettingsFrame(self.content_frame).tkraise()

    def clear_content(self):
        # Clear the content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def validate_numeric_input(self, action, value_if_allowed, text):
        if action == '1':
            return text.isdigit() and int(value_if_allowed) > 0
        return True

if __name__ == "__main__":
    app = ttk.Window("Scale UI", "darkly")
    app.geometry("800x600") 
    Main(app)
    app.mainloop()