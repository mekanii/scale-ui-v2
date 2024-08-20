from pathlib import Path
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.style import Bootstyle


IMG_PATH = Path(__file__).parent / 'assets'


class CollapsingFrame(ttk.Frame):
    """A collapsible frame widget that opens and closes with a click."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)
        self.cumulative_rows = 0

        # widget images
        self.images = [
            ttk.PhotoImage(name='chevron-up-24', file=IMG_PATH/'icons/chevron-up-24.png'),
            ttk.PhotoImage(name='chevron-down-24', file=IMG_PATH/'icons/chevron-down-24.png')
        ]

        self.style = ttk.Style()
        self.style.configure(
            'LeftAligned.TButton',
            anchor=W,
            background=self.style.lookup('TFrame', 'background'),
            foreground='white',
            borderwidth=0,
            font=('Arial', 14)
        )

    def add(self, child, title="", bootstyle=PRIMARY, **kwargs):
        if child.winfo_class() != 'TFrame':
            return

        style_color = Bootstyle.ttkstyle_widget_color(bootstyle)
        frm = ttk.Frame(self, bootstyle=style_color)
        frm.grid(row=self.cumulative_rows, column=0, sticky=EW)

        # header toggle button
        def _func(c=child): return self._toggle_open_close(c)
        btn = ttk.Button(
            master=frm,
            text=title,
            # image=self.images[1],  # Set to the "closed" state image initially
            compound=LEFT,
            bootstyle=style_color,
            command=_func,
            style='LeftAligned.TButton',
            padding=(10, 10)
        )
        if kwargs.get('textvariable'):
            btn.configure(textvariable=kwargs.get('textvariable'))
        btn.pack(fill=BOTH)

        # assign toggle button to child so that it can be toggled
        child.btn = btn
        child.grid(row=self.cumulative_rows + 1, column=0, sticky=NSEW)
        child.grid_remove()  # Hide the child widget initially

        # increment the row assignment
        self.cumulative_rows += 2

    def _toggle_open_close(self, child):
        """Open or close the section and change the toggle button 
        image accordingly.

        Parameters:

            child (Frame):
                The child element to add or remove from grid manager.
        """
        if child.winfo_viewable():
            child.grid_remove()
            # child.btn.configure(image=self.images[1])  # Set to "closed" state image
        else:
            self._collapse_all_except(child)
            child.grid()
            # child.btn.configure(image=self.images[0])  # Set to "open" state image

    def _collapse_all_except(self, exception_child):
        for child in self.winfo_children():
            if isinstance(child, ttk.Frame) and child != exception_child and child.winfo_viewable():
                if hasattr(child, 'btn'):
                    child.grid_remove()
                    # child.btn.config(image=self.images[1])