"""Discipline selection panel component."""

from tkinter import ttk


class DisciplinePanel:
    """
    Panel for selecting active disciplines via checkboxes.

    Allows users to enable/disable disciplines which determines
    which columns appear in the table and which input fields are shown.
    """

    def __init__(self, parent, disciplines, disc_state, on_toggle_callback=None):
        """
        Initialize the discipline panel.

        Args:
            parent: Parent widget
            disciplines: List of Discipline objects
            disc_state: Dict of discipline code -> BooleanVar for active state
            on_toggle_callback: Optional callback when a discipline is toggled
        """
        self.parent = parent
        self.disciplines = disciplines
        self.disc_state = disc_state
        self.on_toggle_callback = on_toggle_callback

        # Frame
        self.frame = ttk.LabelFrame(parent, text="Disciplines", padding=(10, 8))

    def build(self):
        """Build the discipline checkboxes."""
        for idx, d in enumerate(self.disciplines):
            cb = ttk.Checkbutton(
                self.frame,
                text=d.label,
                variable=self.disc_state[d.code],
                command=self._on_toggle
            )
            cb.grid(row=0, column=idx, sticky="w", padx=(0, 12))

    def pack(self, **kwargs):
        """Pack the discipline panel frame."""
        self.frame.pack(**kwargs)

    def _on_toggle(self):
        """Handle discipline checkbox toggle."""
        if self.on_toggle_callback:
            self.on_toggle_callback()
