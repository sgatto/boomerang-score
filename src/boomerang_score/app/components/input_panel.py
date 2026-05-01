"""Input panel component for adding new participants."""

import tkinter as tk
from tkinter import ttk, messagebox


class InputPanel:
    """
    Panel for entering and adding new participant data.

    Provides input fields for name, start number, and result values
    for each active discipline, along with an add button.
    """

    def __init__(self, parent, disciplines, disc_state, service, data, competition, fonts):
        """
        Initialize the input panel.

        Args:
            parent: Parent widget
            disciplines: List of Discipline objects
            disc_state: Dict of discipline code -> BooleanVar for active state
            service: CompetitionService instance
            data: LegacyDataAdapter for participant data
            competition: Competition instance
            fonts: Dict with 'main' and 'bold' fonts
        """
        self.parent = parent
        self.disciplines = disciplines
        self.disc_state = disc_state
        self.service = service
        self.data = data
        self.competition = competition
        self.fonts = fonts

        # Widgets
        self.frame = ttk.LabelFrame(parent, text="Add participant", padding=(10, 8))
        self.ent_name = None
        self.ent_startnr = None
        self.disc_entries = {}  # discipline code -> Entry widget
        self.frm_dyn_inputs = None
        self.on_add_callback = None  # Callback when participant is added
        self.on_delete_callback = None  # Callback when "Delete line" is clicked
        self.on_load_csv_callback = None
        self.on_save_csv_callback = None
        self.on_save_pdf_callback = None
        self.on_overall_awards_callback = None

    def build(self):
        """Build the input panel UI."""
        # Clear existing widgets
        for widget in self.frame.winfo_children():
            widget.destroy()

        frm_input = ttk.Frame(self.frame)
        frm_input.pack(fill="x")

        # Name field
        ttk.Label(frm_input, text="Name:", font=self.fonts['bold']).grid(row=0, column=0, sticky="w")
        self.ent_name = ttk.Entry(frm_input, width=25)
        self.ent_name.grid(row=0, column=1, sticky="w", padx=(6, 12))

        # Start number field
        ttk.Label(frm_input, text="Start No.:", font=self.fonts['bold']).grid(row=0, column=2, sticky="w")
        self.ent_startnr = ttk.Entry(frm_input, width=8)
        self.ent_startnr.grid(row=0, column=3, sticky="w", padx=(6, 12))

        # Dynamic discipline inputs
        self.frm_dyn_inputs = ttk.Frame(frm_input)
        self.frm_dyn_inputs.grid(row=0, column=4, sticky="w")
        self._build_discipline_inputs()

        # Add, Delete and Export buttons
        frm_buttons = ttk.Frame(frm_input)
        frm_buttons.grid(row=1, column=0, columnspan=5, sticky="w", pady=(8, 0))
        ttk.Button(frm_buttons, text="Add line", command=self.on_add).pack(side="left", padx=(0, 12))
        ttk.Button(frm_buttons, text="Delete line", command=self.on_delete).pack(side="left", padx=(0, 12))
        ttk.Button(frm_buttons, text="load CSV", command=self.on_load_csv).pack(side="left", padx=(0, 12))
        ttk.Button(frm_buttons, text="save CSV", command=self.on_save_csv).pack(side="left", padx=(0, 12))
        ttk.Button(frm_buttons, text="save PDF", command=self.on_save_pdf).pack(side="left", padx=(0, 12))
        ttk.Button(frm_buttons, text="Overall awards (PDF/DOCX)", command=self.on_overall_awards).pack(side="left", padx=(0, 12))

        # Configure column weights
        for c in range(4):
            frm_input.grid_columnconfigure(c, weight=0)
        frm_input.grid_columnconfigure(4, weight=1)

    def _build_discipline_inputs(self):
        """Build input fields for active disciplines."""
        # Clear existing
        for widget in self.frm_dyn_inputs.winfo_children():
            widget.destroy()
        self.disc_entries.clear()

        col = 0
        for d in self.disciplines:
            if not self.disc_state[d.code].get():
                continue
            ttk.Label(self.frm_dyn_inputs, text=f"{d.label}:", font=self.fonts['bold']).grid(
                row=0, column=col, sticky="w"
            )
            ent = ttk.Entry(self.frm_dyn_inputs, width=10)
            ent.grid(row=0, column=col + 1, sticky="w", padx=(6, 12))
            self.disc_entries[d.code] = ent
            col += 2

    def rebuild_discipline_inputs(self):
        """Rebuild discipline input fields (e.g., when active disciplines change)."""
        self._build_discipline_inputs()

    def pack(self, **kwargs):
        """Pack the input panel frame."""
        self.frame.pack(**kwargs)

    def set_add_callback(self, callback):
        """Set callback to be called when participant is added."""
        self.on_add_callback = callback

    def set_delete_callback(self, callback):
        """Set callback to be called when Delete line is clicked."""
        self.on_delete_callback = callback

    def set_load_csv_callback(self, callback):
        """Set callback to be called when load CSV is clicked."""
        self.on_load_csv_callback = callback

    def set_save_csv_callback(self, callback):
        """Set callback to be called when save CSV is clicked."""
        self.on_save_csv_callback = callback

    def set_save_pdf_callback(self, callback):
        """Set callback to be called when save PDF is clicked."""
        self.on_save_pdf_callback = callback

    def set_overall_awards_callback(self, callback):
        """Set callback to be called when Overall awards is clicked."""
        self.on_overall_awards_callback = callback

    def on_add(self):
        """Handle add button click."""
        name = self.ent_name.get().strip()
        if not name:
            messagebox.showwarning("Missing Input", "Please enter a name.")
            return

        try:
            startnr = self._parse_int(self.ent_startnr.get())
        except ValueError:
            messagebox.showwarning("Invalid Start Number", "Start number must be an integer.")
            return

        if startnr is None:
            startnr = self.competition.next_free_startnumber()

        # Collect discipline values
        disc_values = {}
        for d in self.disciplines:
            ent = self.disc_entries.get(d.code)
            if ent is None:
                disc_values[d.code] = 0.0
            else:
                try:
                    v = self._parse_float(ent.get())
                    disc_values[d.code] = v if v is not None else 0.0
                except ValueError:
                    messagebox.showwarning("Invalid Input",
                                         f"{d.label}: Result must be a number.")
                    return

        # Notify callback to add participant
        if self.on_add_callback:
            success = self.on_add_callback(name, startnr, disc_values)
            if success:
                self._clear_inputs()

    def on_delete(self):
        """Handle delete button click."""
        if self.on_delete_callback:
            self.on_delete_callback()

    def on_load_csv(self):
        """Handle load CSV button click."""
        if self.on_load_csv_callback:
            self.on_load_csv_callback()

    def on_save_csv(self):
        """Handle save CSV button click."""
        if self.on_save_csv_callback:
            self.on_save_csv_callback()

    def on_save_pdf(self):
        """Handle save PDF button click."""
        if self.on_save_pdf_callback:
            self.on_save_pdf_callback()

    def on_overall_awards(self):
        """Handle Overall awards button click."""
        if self.on_overall_awards_callback:
            self.on_overall_awards_callback()

    def _clear_inputs(self):
        """Clear input fields after successful add."""
        self.ent_startnr.delete(0, "end")
        for ent in self.disc_entries.values():
            ent.delete(0, "end")

    def _parse_float(self, s, allow_empty=True):
        """Parse string to float."""
        s = (s or "").strip()
        if s == "":
            return None if allow_empty else 0.0
        return float(s.replace(",", "."))

    def _parse_int(self, s, allow_empty=True):
        """Parse string to int."""
        s = (s or "").strip()
        if s == "":
            return None if allow_empty else 0
        return int(s)
