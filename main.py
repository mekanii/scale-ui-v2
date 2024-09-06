from pathlib import Path
from PIL import Image
Image.CUBIC = Image.BICUBIC

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.toast import ToastNotification
from ttkbootstrap.style import Colors
from ttkbootstrap.style import Style
import tkinter as tk
import tkinter.font as tkFont
import serial
import serial.tools.list_ports
import json
import ast
import time

from globalvar import GlobalConfig
from scale import ScaleFrame
from parts import PartsFrame
from summary import SummaryFrame
from calibration import CalibrationFrame

PATH = Path(__file__).parent / 'assets'

class Main(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.create_toolbutton_style(colorname=SECONDARY)
        self.create_button_style(colorname=INFO)
        self.create_button_style(colorname=DANGER)
        self.create_button_style(colorname=SUCCESS)
        self.create_button_style(colorname=SECONDARY)
        self.create_menubutton_style(colorname=SECONDARY)
        self.create_combobox_style(colorname=SECONDARY)

        self.option_add('*TCombobox*Listbox.font', ('Segoe UI', 20))

        self.pack(expand=True, fill=BOTH)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0, minsize=350)
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
                file=PATH / 'icons/cog-36.png'),
            ttk.PhotoImage(
                name='target-lock-36',
                file=PATH / 'icons/target-lock-36.png'),
            ttk.PhotoImage(
                name='sync-36',
                file=PATH / 'icons/sync-36.png'),
            ttk.PhotoImage(
                name='cast-36',
                file=PATH / 'icons/cast-36.png'),
            ttk.PhotoImage(
                name='tachometer-36',
                file=PATH / 'icons/tachometer-36.png'),
            ttk.PhotoImage(
                name='circle-36',
                file=PATH / 'icons/circle-36.png'),
            ttk.PhotoImage(
                name='chevron-up-24',
                file=PATH / 'icons/chevron-up-24.png'),
            ttk.PhotoImage(
                name='chevron-down-24',
                file=PATH / 'icons/chevron-down-24.png'),
            ttk.PhotoImage(
                name='reset-36',
                file=PATH / 'icons/reset-36.png'),
            ttk.PhotoImage(
                name='add-circle-36',
                file=PATH / 'icons/add-circle-36.png'),
            ttk.PhotoImage(
                name='play-circle-36',
                file=PATH / 'icons/play-circle-36.png'),
            ttk.PhotoImage(
                name='arrow-circle-down-36',
                file=PATH / 'icons/arrow-circle-down-36.png'),
            ttk.PhotoImage(
                name='downloading-36',
                file=PATH / 'icons/downloading-36.png'),
        ]

        self.popups = {
            "com": None
        }

        GlobalConfig.select_com_options = GlobalConfig.get_available_com_ports()
        
        self.menu_selected = tk.StringVar(value='summary')
        self.com_port = tk.StringVar(value='Select Port')

        # menu buttons
        menu_frame = ttk.Frame(self, bootstyle=SECONDARY)
        menu_frame.grid(row=0, column=0, sticky=NSEW)
        menu_frame.grid_propagate(False)

        self.select_com_combobox = ttk.Combobox(
            master=menu_frame,
            values=GlobalConfig.select_com_options,
            textvariable=self.com_port,
            state=READONLY,
            style='Secondary.TCombobox',
            font=('Segoe UI', 20)
        )
        self.select_com_combobox.pack(side=TOP, fill=BOTH, pady=(20, 0))
        self.select_com_combobox.bind('<<ComboboxSelected>>', self.combobox_select)

        # self.select_com_combobox = ttk.Menubutton(
        #     master=menu_frame,
        #     text="Select Port",
        #     style='Secondary.TMenubutton'
        # )
        # self.select_com_combobox.pack(side=TOP, fill=BOTH, ipady=10, pady=(20, 10))
        # # self.select_com_combobox.bind('<Button-1>', lambda event: self.toggle_popup("com", self.select_com_combobox, GlobalConfig.select_com_options, GlobalConfig.com_port))
        # self.com_menu = ttk.Menu(menu_frame, font=('Segoe UI', 20))
        # self.create_menu(self.select_com_combobox, self.com_menu, GlobalConfig.select_com_options, GlobalConfig.com_port)
        # self.create_popup(self.select_com_combobox, "com", GlobalConfig.select_com_options, GlobalConfig.com_port)

        self.connect_button = ttk.Button(
            master=menu_frame,
            image='cast-36',
            text='  Connect',
            style='Info.TButton',
            command=self.toggle_connect
        )
        self.connect_button.pack(side=TOP, fill=BOTH)

        self.menu_summary_btn = ttk.Radiobutton(
            master=menu_frame,
            image='book-36',
            text='  Summary',
            value='summary',
            variable=self.menu_selected,
            state=NORMAL,
            compound=LEFT,
            # bootstyle=TOOLBUTTON,
            style='Secondary.Toolbutton',
            command=lambda: self.show_summary()
        )
        self.menu_summary_btn.pack(side=TOP, fill=BOTH, ipady=10, pady=(20, 0))

        self.menu_main_btn = ttk.Radiobutton(
            master=menu_frame,
            image='tachometer-36',
            text='  Main',
            value='main',
            variable=self.menu_selected,
            state=DISABLED,
            compound=LEFT,
            # bootstyle=TOOLBUTTON,
            style='Secondary.Toolbutton',
            command=lambda: self.show_scale()
        )
        self.menu_main_btn.pack(side=TOP, fill=BOTH, ipady=10)

        self.menu_parts_btn = ttk.Radiobutton(
            master=menu_frame,
            image='device-36',
            text='  Parts',
            value='parts',
            variable=self.menu_selected,
            state=DISABLED,
            compound=LEFT,
            # bootstyle=TOOLBUTTON,
            style='Secondary.Toolbutton',
            command=lambda: self.show_parts()
        )
        self.menu_parts_btn.pack(side=TOP, fill=BOTH, ipady=10)


        self.menu_calibration_btn = ttk.Radiobutton(
            master=menu_frame,
            image='target-lock-36',
            text='  Calibration',
            value='calibration',
            variable=self.menu_selected,
            state=DISABLED,
            compound=LEFT,
            # bootstyle=TOOLBUTTON,
            style='Secondary.Toolbutton',
            command=lambda: self.show_calibration()
        )
        self.menu_calibration_btn.pack(side=TOP, fill=BOTH, ipady=10)

        self.content_frame = ttk.Frame(self)
        self.content_frame.grid(row=0, column=1, sticky=NSEW, padx=5, pady=5)
        self.content_frame.grid_rowconfigure(0, weight=1)  # Add this line
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.show_summary()

        self.update_com_ports()

        # if GlobalConfig.serial_connection and GlobalConfig.serial_connection.is_open:
        #     self.select_com_combobox.config(text=GlobalConfig.com_port)
        #     self.toggle_connect()
        

    def show_scale(self):
        self.clear_content()
        ScaleFrame(self.content_frame).tkraise()

    def show_parts(self):
        self.clear_content()
        PartsFrame(self.content_frame).tkraise()

    def show_summary(self):
        self.clear_content()
        SummaryFrame(self.content_frame).tkraise()

    def show_calibration(self):
        self.clear_content()
        CalibrationFrame(self.content_frame).tkraise()

    def clear_content(self):
        # Clear the content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def validate_numeric_input(self, action, value_if_allowed, text):
        if action == '1':
            return text.isdigit() and int(value_if_allowed) > 0
        return True
    
    def create_menu(self, widget, menu, options, variable):
        for option in options:
            menu.add_command(
                label=option["name"] if isinstance(option, dict) else option,
                command=lambda opt=option: self.select_option(widget, menu, opt, variable)
            )
        widget.config(menu=menu)

    def combobox_select(self, event):
        GlobalConfig.com_port = event.widget.get().replace('    ', '')
        self.com_port.set(GlobalConfig.com_port)

    def update_com_ports(self):
        # Check if the connect_button text is "CONNECT"
        if self.connect_button.cget("text") == "  Connect":
            new_com_ports = GlobalConfig.get_available_com_ports()
            if new_com_ports != GlobalConfig.select_com_options:
                GlobalConfig.select_com_options = new_com_ports

                self.select_com_combobox.config(values=GlobalConfig.select_com_options)
                
                # Update the popup if it's currently visible
                # if self.popups["com"] and self.popups["com"].winfo_exists():
                    # self.create_popup(self.select_com_combobox, "com", GlobalConfig.select_com_options, GlobalConfig.com_port)
                    # self.create_menu(self.select_com_combobox, self.com_menu, GlobalConfig.select_com_options, GlobalConfig.com_port)
        # Schedule the next update
        self.after(1000, self.update_com_ports)  # Update every second

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
          # Reference the global variable
        if GlobalConfig.serial_connection and GlobalConfig.serial_connection.is_open:
            GlobalConfig.serial_connection.close()
            GlobalConfig.serial_connection = None
            return True
        return False    
    
    def toggle_connect(self):
        current_text = self.connect_button.cget("text")
        if current_text == "  Connect":
            if GlobalConfig.com_port == "":
                return
            print(GlobalConfig.com_port)
            if self.connect_to_com_port():
                self.connect_button.config(text="  Disconnect", bootstyle="DANGER")
                self.select_com_combobox.config(state=DISABLED)
                self.menu_main_btn.config(state=NORMAL)
                self.menu_parts_btn.config(state=NORMAL)
                self.menu_calibration_btn.config(state=NORMAL)
                
        else:
            if self.disconnect_from_com_port():
                self.connect_button.config(text="  Connect", bootstyle="INFO")
                self.select_com_combobox.config(state=READONLY)
                self.menu_main_btn.config(state=DISABLED)
                self.menu_parts_btn.config(state=DISABLED)
                self.menu_calibration_btn.config(state=DISABLED)
                self.menu_selected.set('summary')
                self.clear_content()
                self.show_summary()

    def notificatiion(self, title, message, status):
        toast = ToastNotification(
            title=title,
            message=message,
            duration=1500,
            bootstyle=SUCCESS if status else DANGER,
            position=(self.winfo_rootx(), self.winfo_rooty(), NW)
        )
        toast.show_toast()
    
    def create_button_style(self, colorname=DEFAULT):
        """Create a solid style for the ttk.Button widget.

        Parameters:

            colorname (str):
                The color label used to style the widget.
        """
        STYLE = "TButton"
        style = Style()

        if any([colorname == DEFAULT, colorname == ""]):
            ttkstyle = STYLE
            foreground = style.colors.get_foreground(PRIMARY)
            background = style.colors.primary
        else:
            ttkstyle = f"{colorname}.{STYLE}"
            foreground = style.colors.get_foreground(colorname)
            background = style.colors.get(colorname)

        bordercolor = background
        disabled_bg = Colors.make_transparent(0.10, style.colors.fg, style.colors.bg)
        disabled_fg = Colors.make_transparent(0.30, style.colors.fg, style.colors.bg)
        pressed = Colors.make_transparent(0.80, background, style.colors.bg)
        hover = Colors.make_transparent(0.90, background, style.colors.bg)        

        style._build_configure(
            ttkstyle,
            foreground=foreground,
            background=background,
            bordercolor=bordercolor,
            darkcolor=background,
            lightcolor=background,
            relief=tk.RAISED,
            focusthickness=0,
            focuscolor=foreground,
            padding=(10, 5),
            compound=tk.LEFT,
            anchor=tk.W,
            font=('Segoe UI', 20)
        )
        style.map(
            ttkstyle,
            foreground=[("disabled", disabled_fg)],
            background=[
                ("disabled", disabled_bg),
                ("pressed !disabled", pressed),
                ("hover !disabled", hover),
            ],
            bordercolor=[("disabled", disabled_bg)],
            darkcolor=[
                ("disabled", disabled_bg),
                ("pressed !disabled", pressed),
                ("hover !disabled", hover),
            ],
            lightcolor=[
                ("disabled", disabled_bg),
                ("pressed !disabled", pressed),
                ("hover !disabled", hover),
            ],
        )
        # register ttkstyle
        style._register_ttkstyle(ttkstyle)

    def create_menubutton_style(self, colorname=DEFAULT):
        """Create a solid style for the ttk.Menubutton widget.

        Parameters:

            colorname (str):
                The color label used to style the widget.
        """
        STYLE = "TMenubutton"
        style = Style()

        foreground = style.colors.get_foreground(colorname)

        if any([colorname == DEFAULT, colorname == ""]):
            ttkstyle = STYLE
            background = style.colors.primary
        else:
            ttkstyle = f"{colorname}.{STYLE}"
            background = style.colors.get(colorname)

        disabled_bg = Colors.make_transparent(0.10, style.colors.fg, style.colors.bg)
        disabled_fg = Colors.make_transparent(0.30, style.colors.fg, style.colors.bg)
        pressed = Colors.make_transparent(0.80, background, style.colors.bg)
        hover = Colors.make_transparent(0.90, background, style.colors.bg)    

        style._build_configure(
            ttkstyle,
            foreground=foreground,
            background=background,
            bordercolor=background,
            darkcolor=background,
            lightcolor=background,
            arrowsize=ttk.utility.scale_size(self, 8),
            arrowcolor=foreground,
            arrowpadding=(0, 0, 15, 0),
            relief=tk.FLAT,
            focusthickness=0,
            focuscolor=style.colors.selectfg,
            padding=(10, 5),
            font=('Segoe UI', 20)
        )
        style.map(
            ttkstyle,
            arrowcolor=[("disabled", disabled_fg)],
            foreground=[("disabled", disabled_fg)],
            background=[
                ("disabled", disabled_bg),
                ("pressed !disabled", pressed),
                ("hover !disabled", hover),
            ],
            bordercolor=[
                ("disabled", disabled_bg),
                ("pressed !disabled", pressed),
                ("hover !disabled", hover),
            ],
            darkcolor=[
                ("disabled", disabled_bg),
                ("pressed !disabled", pressed),
                ("hover !disabled", hover),
            ],
            lightcolor=[
                ("disabled", disabled_bg),
                ("pressed !disabled", pressed),
                ("hover !disabled", hover),
            ],
        )
        # register ttkstyle
        style._register_ttkstyle(ttkstyle)

    def create_toolbutton_style(self, colorname=DEFAULT):
        """Create a solid toolbutton style for the ttk.Checkbutton
        and ttk.Radiobutton widgets.

        Parameters:

            colorname (str):
                The color label used to style the widget.
        """
        STYLE = "Toolbutton"
        style = Style()

        if any([colorname == DEFAULT, colorname == ""]):
            ttkstyle = STYLE
            toggle_on = style.colors.primary
        else:
            ttkstyle = f"{colorname}.{STYLE}"
            toggle_on = style.colors.get(colorname)

        foreground = style.colors.get_foreground(colorname)
        hover = style.colors.selectbg

        # if is_light_theme:
        #     toggle_off = style.colors.border
        # else:
        toggle_off = style.colors.get(SECONDARY)

        disabled_bg = Colors.make_transparent(0.10, style.colors.fg, style.colors.bg)
        disabled_fg = Colors.make_transparent(0.30, style.colors.fg, style.colors.bg)

        style._build_configure(
            ttkstyle,
            foreground=style.colors.selectfg,
            background=toggle_off,
            bordercolor=toggle_off,
            darkcolor=toggle_off,
            lightcolor=toggle_off,
            relief=tk.FLAT,
            focusthickness=0,
            focuscolor="",
            padding=(10, 5),
            anchor=tk.W,
            font=('Segoe UI', 20)
        )
        style.map(
            ttkstyle,
            foreground=[
                ("disabled", disabled_fg),
                ("hover", foreground),
                ("selected", foreground),
            ],
            background=[
                ("disabled", disabled_bg),
                ("pressed !disabled", toggle_on),
                ("selected !disabled", toggle_on),
                ("hover !disabled", hover),
            ],
            bordercolor=[
                ("disabled", disabled_bg),
                ("pressed !disabled", toggle_on),
                ("selected !disabled", toggle_on),
                ("hover !disabled", hover),
            ],
            darkcolor=[
                ("disabled", disabled_bg),
                ("pressed !disabled", toggle_on),
                ("selected !disabled", toggle_on),
                ("hover !disabled", hover),
            ],
            lightcolor=[
                ("disabled", disabled_bg),
                ("pressed !disabled", toggle_on),
                ("selected !disabled", toggle_on),
                ("hover !disabled", hover),
            ],
        )
        # register ttkstyle
        style._register_ttkstyle(ttkstyle)

    def create_menubutton_style(self, colorname=DEFAULT):
        """Create a solid style for the ttk.Menubutton widget.

        Parameters:

            colorname (str):
                The color label used to style the widget.
        """
        STYLE = "TMenubutton"
        style = Style()

        foreground = style.colors.get_foreground(colorname)

        if any([colorname == DEFAULT, colorname == ""]):
            ttkstyle = STYLE
            background = style.colors.primary
        else:
            ttkstyle = f"{colorname}.{STYLE}"
            background = style.colors.get(colorname)

        disabled_bg = Colors.make_transparent(0.10, style.colors.fg, style.colors.bg)
        disabled_fg = Colors.make_transparent(0.30, style.colors.fg, style.colors.bg)
        pressed = Colors.make_transparent(0.80, background, style.colors.bg)
        hover = Colors.make_transparent(0.90, background, style.colors.bg)    

        style._build_configure(
            ttkstyle,
            foreground=foreground,
            background=background,
            bordercolor=background,
            darkcolor=background,
            lightcolor=background,
            arrowsize=ttk.utility.scale_size(self, 8),
            arrowcolor=foreground,
            arrowpadding=(0, 0, 15, 0),
            relief=tk.FLAT,
            focusthickness=0,
            focuscolor=style.colors.selectfg,
            padding=(10, 5),
            font=('Segoe UI', 20)
        )
        style.map(
            ttkstyle,
            arrowcolor=[("disabled", disabled_fg)],
            foreground=[("disabled", disabled_fg)],
            background=[
                ("disabled", disabled_bg),
                ("pressed !disabled", pressed),
                ("hover !disabled", hover),
            ],
            bordercolor=[
                ("disabled", disabled_bg),
                ("pressed !disabled", pressed),
                ("hover !disabled", hover),
            ],
            darkcolor=[
                ("disabled", disabled_bg),
                ("pressed !disabled", pressed),
                ("hover !disabled", hover),
            ],
            lightcolor=[
                ("disabled", disabled_bg),
                ("pressed !disabled", pressed),
                ("hover !disabled", hover),
            ],
        )
        # register ttkstyle
        style._register_ttkstyle(ttkstyle)

    def create_combobox_style(self, colorname=DEFAULT):
        """Create a style for the ttk.Combobox widget.

        Parameters:

            colorname (str):
                The color label to use as the primary widget color.
        """
        STYLE = "TCombobox"
        style = Style()

        # if self.is_light_theme:
        #     disabled_fg = style.colors.border
        #     bordercolor = style.colors.border
        #     readonly = style.colors.light
        # else:
        disabled_fg = style.colors.selectbg
        bordercolor = style.colors.selectbg
        readonly = bordercolor

        if any([colorname == DEFAULT, colorname == ""]):
            ttkstyle = STYLE
            element = f"{ttkstyle.replace('TC','C')}"
            focuscolor = style.colors.primary
        else:
            ttkstyle = f"{colorname}.{STYLE}"
            element = f"{ttkstyle.replace('TC','C')}"
            focuscolor = style.colors.get(colorname)

        style.element_create(f"{element}.downarrow", "from", TTK_DEFAULT)
        style.element_create(f"{element}.padding", "from", TTK_CLAM)
        style.element_create(f"{element}.textarea", "from", TTK_CLAM)

        if all([colorname, colorname != DEFAULT]):
            bordercolor = focuscolor

        style._build_configure(
            ttkstyle,
            bordercolor=bordercolor,
            darkcolor=style.colors.inputbg,
            lightcolor=style.colors.inputbg,
            arrowcolor=style.colors.fg,
            foreground=style.colors.inputfg,
            fieldbackground=style.colors.inputbg,
            background=style.colors.inputbg,
            insertcolor=style.colors.inputfg,
            relief=tk.FLAT,
            padding=(20, 12),
            arrowsize=ttk.utility.scale_size(self, 24),
        )
        style.map(
            ttkstyle,
            background=[("readonly", readonly)],
            fieldbackground=[("readonly", readonly)],
            foreground=[("disabled", disabled_fg)],
            bordercolor=[
                ("invalid", style.colors.danger),
                ("focus !disabled", focuscolor),
                ("hover !disabled", focuscolor),
            ],
            lightcolor=[
                ("focus invalid", style.colors.danger),
                ("focus !disabled", focuscolor),
                ("pressed !disabled", focuscolor),
                ("readonly", readonly),
            ],
            darkcolor=[
                ("focus invalid", style.colors.danger),
                ("focus !disabled", focuscolor),
                ("pressed !disabled", focuscolor),
                ("readonly", readonly),
            ],
            arrowcolor=[
                ("disabled", disabled_fg),
                ("pressed !disabled", style.colors.fg),
                ("focus !disabled", style.colors.fg),
                ("hover !disabled", style.colors.fg),
            ],
        )
        style.layout(
            ttkstyle,
            [
                (
                    "combo.Spinbox.field",
                    {
                        "side": tk.TOP,
                        "sticky": tk.EW,
                        "children": [
                            (
                                "Combobox.downarrow",
                                {"side": tk.RIGHT, "sticky": tk.NS},
                            ),
                            (
                                "Combobox.padding",
                                {
                                    "expand": "1",
                                    "sticky": tk.NSEW,
                                    "children": [
                                        (
                                            "Combobox.textarea",
                                            {"sticky": tk.NSEW},
                                        )
                                    ],
                                },
                            ),
                        ],
                    },
                )
            ],
        )

        style._register_ttkstyle(ttkstyle)
        

if __name__ == "__main__":
    app = ttk.Window("Scale UI", "darkly")
    app.geometry("1366x768") 
    Main(app)
    app.mainloop()