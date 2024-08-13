import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk

class SettingsFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)

        label = ttk.Label(self, text="Settings Frame", font=("Arial", 24))
        label.grid(row=0, column=0, padx=10, pady=10)