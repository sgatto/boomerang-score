"""
Boomerang Scoring Application - Refactored Version

Main application with separated GUI components.
"""

import os
import sys

# Fix for [xcb] Unknown sequence number while appending request
if sys.platform.startswith("linux"):
    try:
        import ctypes
        x11 = ctypes.cdll.LoadLibrary("libX11.so.6")
        x11.XInitThreads()
    except Exception:
        pass
    os.environ["LIBXCB_ALLOW_SLOPPY_LOCK"] = "1"

from boomerang_score.core import Competition, Participant, ACC, AUS, MTA, END, FC, TC, TIMED, TAPIR
from boomerang_score.services import CompetitionService, ExportService
from boomerang_score.app.adapter import LegacyDataAdapter
from boomerang_score.app.components import ParticipantTableView, InputPanel, DisciplinePanel, MenuBar

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Constants
BASE_COLUMNS = ["name", "startnumber", "total", "overall_rank"]
EVENTS = ["ACC", "AUS", "MTA", "END", "FC", "TC", "TIMED", "TAPIR"]
SORTED = ["StartNr", "Rank"]

# Discipline Configuration
DISCIPLINES = [
    ACC,
    AUS,
    MTA,
    END,
    FC,
    TC,
    TIMED,
    TAPIR,
]


class ScoreTableApp(tk.Tk):
    """
    Main application window for boomerang scoring.

    Uses component-based architecture:
    - DisciplinePanel: Select active disciplines
    - InputPanel: Add new participants
    - ParticipantTableView: Display and edit participant data
    - MenuBar: Access export and view options
    """

    def __init__(self):
        super().__init__()
        from tkinter import font

        self.title("Scoring Table – Dynamic Disciplines")
        self.geometry("1450x720")

        # Core models and services
        self.competition = Competition()
        self.service = CompetitionService(self.competition, DISCIPLINES)
        self.export_service = ExportService(self.competition, DISCIPLINES)

        # Legacy adapter
        self.data = LegacyDataAdapter(self.competition, self.service)

        # Discipline state
        self.disc_state = {d.code: tk.BooleanVar(value=d.default_active) for d in DISCIPLINES}

        # Initialize active disciplines
        active = {d.code for d in DISCIPLINES if d.default_active}
        self.service.set_active_disciplines(active)

        # Font configuration
        self.style = ttk.Style(self)
        available_fonts = list(font.families())
        font_preferences = [
            "DejaVu Sans", "Liberation Sans", "Noto Sans", "Ubuntu",
            "Cantarell", "FreeSans", "Helvetica", "Arial", "sans-serif"
        ]
        chosen_family = "TkDefaultFont"
        for preferred in font_preferences:
            if preferred in available_fonts:
                chosen_family = preferred
                break

        self.font_main = font.Font(family=chosen_family, size=-14)
        self.font_bold = font.Font(family=chosen_family, size=-14, weight="bold")
        self.font_title = font.Font(family=chosen_family, size=-18, weight="bold")

        self.style.configure("Treeview", font=self.font_main, rowheight=24)
        self.style.configure("Treeview.Heading", font=self.font_bold)

        # GUI Components
        self.discipline_panel = None
        self.input_panel = None
        self.table_view = None
        self.menu_bar = None

        # Build UI
        self._build_ui()

    def _build_ui(self):
        """Build the main UI layout."""
        # Main Canvas with scrollbars for the whole window
        self.main_canvas = tk.Canvas(self, highlightthickness=0)

        self.v_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.main_canvas.yview)
        self.v_scrollbar.pack(side="right", fill="y")
        self.h_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.main_canvas.xview)
        self.h_scrollbar.pack(side="bottom", fill="x")

        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.main_canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)

        # Frame inside canvas
        self.main_frame = ttk.Frame(self.main_canvas)
        self.main_canvas.create_window((0, 0), window=self.main_frame, anchor="nw")

        def _on_frame_configure(event):
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

        self.main_frame.bind("<Configure>", _on_frame_configure)

        def _on_mousewheel(event):
            if sys.platform.startswith("win"):
                self.main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            else:
                if event.num == 4:
                    self.main_canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.main_canvas.yview_scroll(1, "units")

        self.main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.main_canvas.bind_all("<Button-4>", _on_mousewheel)
        self.main_canvas.bind_all("<Button-5>", _on_mousewheel)

        # Menu bar
        self.menu_bar = MenuBar(self, self.export_service, None, self.competition)

        # Title + Logo section
        frm_title = ttk.Frame(self.main_frame, padding=(10, 6))
        frm_title.pack(fill="x")

        ttk.Label(frm_title, text="Competition Title:").grid(row=0, column=0, sticky="w")
        self.ent_title = ttk.Entry(frm_title, width=60)
        self.ent_title.grid(row=0, column=1, sticky="w", padx=(6, 12))
        self.ent_title.insert(0, self.competition.title)

        self.lbl_title_display = ttk.Label(frm_title, text=self.competition.title, font=self.font_title)
        self.lbl_title_display.grid(row=1, column=0, columnspan=5, sticky="w", pady=(6, 2))

        def update_title(*_):
            self.competition.title = self.ent_title.get()
            self.lbl_title_display.config(text=self.competition.title)
        self.ent_title.bind("<KeyRelease>", update_title)

        ttk.Label(frm_title, text="Logo:").grid(row=0, column=2, sticky="e")
        self.lbl_logo_name = ttk.Label(frm_title, text="(no logo selected)")
        self.lbl_logo_name.grid(row=0, column=3, sticky="w", padx=(6, 6))
        ttk.Button(frm_title, text="Choose logo…", command=self.on_choose_logo).grid(row=0, column=4, sticky="w")

        # Discipline Panel
        fonts = {'main': self.font_main, 'bold': self.font_bold}
        self.discipline_panel = DisciplinePanel(self.main_frame, DISCIPLINES, self.disc_state, self._on_toggle_disciplines)
        self.discipline_panel.build()
        self.discipline_panel.pack(fill="x", padx=10, pady=(0, 6))

        # Input Panel
        self.input_panel = InputPanel(self.main_frame, DISCIPLINES, self.disc_state, self.service,
                                      self.data, self.competition, fonts)
        self.input_panel.build()
        self.input_panel.set_add_callback(self._on_add_participant)
        self.input_panel.set_delete_callback(lambda: self.table_view._on_delete_selected())
        self.input_panel.set_save_csv_callback(self.export_csv)
        self.input_panel.set_save_pdf_callback(self.export_pdf)
        self.input_panel.set_overall_awards_callback(self.export_individual_reports)
        self.input_panel.pack(fill="x", padx=10, pady=(0, 6))

        # Scoresheet section
        frm_scoresheet = ttk.LabelFrame(self.main_frame, text="Scoresheet", padding=(10, 8))
        frm_scoresheet.pack(fill="x", padx=10, pady=(0, 6))

        ttk.Label(frm_scoresheet, text="Number of circles:").grid(row=0, column=0, sticky="w")
        self.ent_circle = ttk.Entry(frm_scoresheet, width=10)
        self.ent_circle.grid(row=0, column=1, sticky="w", padx=(6, 12))
        self.ent_circle.insert(0, "2")

        ttk.Label(frm_scoresheet, text="Event:").grid(row=0, column=2, sticky="w", padx=(20, 6))
        self.event_var = tk.StringVar(value=EVENTS[0])
        ttk.OptionMenu(frm_scoresheet, self.event_var, self.event_var.get(), *EVENTS).grid(row=0, column=3, sticky="w")

        ttk.Label(frm_scoresheet, text="Sorted by").grid(row=0, column=4, sticky="w", padx=(20, 6))
        self.sheetsort_var = tk.StringVar(value=SORTED[0])
        ttk.OptionMenu(frm_scoresheet, self.sheetsort_var, self.sheetsort_var.get(), *SORTED).grid(row=0, column=5, sticky="w")

        ttk.Button(frm_scoresheet, text="print scoresheets",
                  command=self.export_scoresheet).grid(row=0, column=6, padx=(12, 0))

        # Table View
        self.table_view = ParticipantTableView(self.main_frame, DISCIPLINES, self.disc_state,
                                              self.data, self.service, fonts)
        self.table_view.build()
        self.table_view.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Update menu bar with table view reference
        self.menu_bar.table_view = self.table_view
        self.menu_bar.build()

        # Bind keyboard shortcuts for inline editing
        self.bind("<Return>", lambda e: self.table_view.commit_inline_edit())
        self.bind("<KP_Enter>", lambda e: self.table_view.commit_inline_edit())
        self.bind("<Escape>", lambda e: self.table_view.cancel_inline_edit())

    def on_choose_logo(self):
        """Handle logo file selection."""
        path = filedialog.askopenfilename(
            title="Select Logo File",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("All files", "*.*")],
        )
        if path:
            self.competition.logo_path = path
            self.lbl_logo_name.config(text=os.path.basename(path))

    def _on_toggle_disciplines(self):
        """Handle discipline checkbox toggle."""
        # Update active disciplines in service
        active = {d.code for d in DISCIPLINES if self.disc_state[d.code].get()}
        self.service.set_active_disciplines(active)

        # Rebuild components
        self.input_panel.rebuild_discipline_inputs()
        self.table_view.build()

        # Re-insert existing data
        for startnr in self.data.keys():
            self.table_view.tree.insert("", "end", iid=str(startnr), values=[""] * len(self.table_view.all_columns))
            self.table_view.update_row(str(startnr))

    def _on_add_participant(self, name, startnr, disc_values):
        """Handle adding a new participant."""
        try:
            participant = self.service.add_participant(name, startnr, disc_values)

            # Insert row in tree using startnumber as ID
            iid = str(participant.startnumber)
            self.table_view.tree.insert("", "end", iid=iid, values=[""] * len(self.table_view.all_columns))
            self.table_view.update_all_rows()
            return True
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return False

    def export_csv(self):
        """Export visible columns to CSV."""
        filename = filedialog.asksaveasfilename(
            title="Save CSV",
            defaultextension=".csv",
            filetypes=[("CSV file", "*.csv")]
        )
        if not filename:
            return

        try:
            cols = list(self.table_view.tree["displaycolumns"])
            participant_order = list(self.table_view.tree.get_children())
            self.export_service.export_csv(filename, cols, self.table_view.column_headers, participant_order)
            messagebox.showinfo("Export Successful", f"The CSV has been saved:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred:\n{e}")

    def export_pdf(self):
        """Export full list to PDF."""
        filename = filedialog.asksaveasfilename(
            title="Save PDF",
            defaultextension=".pdf",
            filetypes=[("PDF file", "*.pdf")]
        )
        if not filename:
            return

        try:
            participant_order = list(self.table_view.tree.get_children())
            self.export_service.export_pdf_full_list(filename, participant_order)
            messagebox.showinfo("Export Successful", f"The PDF has been saved:\n{filename}")
        except Exception as e:
            messagebox.showerror("PDF Error", f"An error occurred while creating the PDF:\n{e}")

    def export_individual_reports(self):
        """Export individual participant reports."""
        if not self.data:
            messagebox.showwarning("No Data", "There are no participants.")
            return

        out_file = filedialog.asksaveasfilename(
            title="Save Report",
            defaultextension=".pdf",
            filetypes=[("PDF File", "*.pdf"), ("Word Document", "*.docx")]
        )
        if not out_file:
            return

        try:
            participant_order = sorted(
                self.data.keys(),
                key=lambda pid: (self.data[pid].get("overall_rank") or 10**9, self.data[pid].get("name") or "")
            )
            self.export_service.export_individual_reports(out_file, participant_order, self.competition.logo_path)
            messagebox.showinfo("Export Successful", f"Report saved:\n{out_file}")
        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred:\n{e}")

    def export_scoresheet(self):
        """Export scoresheet for a specific event."""
        if not self.data:
            messagebox.showwarning("No Data", "There are no participants.")
            return

        try:
            num_circles = int(self.ent_circle.get().strip() or "1")
            if num_circles < 1:
                num_circles = 1
        except (ValueError, AttributeError):
            num_circles = 1

        sort_method = self.sheetsort_var.get()
        event = self.event_var.get()

        out_file = filedialog.asksaveasfilename(
            title="Save Scoresheet",
            defaultextension=".docx",
            filetypes=[
                ("Word Document", "*.docx"),
                ("PDF File", "*.pdf")
            ]
        )
        if not out_file:
            return

        # Prepare participant order based on sort method
        if sort_method == "Rank":
            participant_order = sorted(
                self.data.keys(),
                key=lambda pid: (self.data[pid].get("overall_rank") or 10**9, self.data[pid].get("name") or "")
            )
        else:
            participant_order = sorted(
                self.data.keys(),
                key=lambda pid: (int(self.data[pid].get("startnummer") or 999), self.data[pid].get("name") or "")
            )

        try:
            self.export_service.export_scoresheet(
                out_file, event, num_circles, sort_method, participant_order
            )
            messagebox.showinfo("Export Successful", f"Scoresheet saved:\n{out_file}")
        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred:\n{e}")


if __name__ == "__main__":
    app = ScoreTableApp()
    app.mainloop()
