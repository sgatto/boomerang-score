
# rss8.py
# Vollständige Anwendung mit dynamischen Disziplinen, Inline-Edit, CSV/PDF-Export und Logo-Unterstützung.

import os
import sys

# Fix for [xcb] Unknown sequence number while appending request
if sys.platform.startswith("linux"):
    # Ensure XInitThreads is called before any X11-related library is loaded (like Tkinter).
    try:
        import ctypes
        x11 = ctypes.cdll.LoadLibrary("libX11.so.6")
        x11.XInitThreads()
    except Exception:
        pass
    # Setting this environment variable helps with X11/XCB sync issues
    os.environ["LIBXCB_ALLOW_SLOPPY_LOCK"] = "1"

from boomerang_score.core import Competition, Participant, ACC, AUS, MTA, END, FC, TC, TIMED
from boomerang_score.services import CompetitionService, ExportService
from boomerang_score.app.adapter import LegacyDataAdapter

import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ==============================
# Constants
# ==============================
BASE_COLUMNS = ["name", "startnumber", "total", "overall_rank"]
EVENTS = ["ACC", "AUS", "MTA", "END", "FC", "TC", "TIMED"]
SORTED = ["StartNr", "Rank"]

# ==============================
# Main App
# ==============================
class ScoreTableApp(tk.Tk):
    """
    Dynamic competition list with discipline selection:
      - Base: Name | Start Number | Total Points | Overall Rank
      - Per active discipline: RES_[XX] | PTS_[XX] | RANK_[XX]

    - Inline-Edit: Name, Start Number, and all active RES values
    - Sorting: via click, toggle, numeric for numbers
    - CSV-Export: exports currently visible columns (displaycolumns)
    - PDF (Full list): A4 landscape, active disciplines
    - PDF (Individual reports): A4, compact table per participant, logo on the right
    """

    def __init__(self):
        super().__init__()
        
        # Necessary imports for dynamic font detection
        from tkinter import font
        
        self.title("Scoring Table – Dynamic Disciplines")
        self.geometry("1450x720")

        # Core models and services
        self.competition = Competition()
        self.service = CompetitionService(self.competition, DISCIPLINES)
        self.export_service = ExportService(self.competition, DISCIPLINES)

        # Legacy adapter - allows old code to work with new models
        self.data = LegacyDataAdapter(self.competition, self.service)

        # Discipline status + entry fields
        self.disc_state = {d.code: tk.BooleanVar(value=d.default_active) for d in DISCIPLINES}
        self.disc_entries = {}  # code -> tk.Entry (Add area)

        # Initialize active disciplines
        active = {d.code for d in DISCIPLINES if d.default_active}
        self.service.set_active_disciplines(active)

        # Tree/Columns
        self.tree = None
        self.all_columns = []        # complete column list (including invisible)
        self.display_columns = []    # currently visible columns
        self.column_visibility = {}  # key -> bool
        self.sort_state = {}         # Column -> ascending?

        # Inline-Editor
        self._edit_entry = None
        self._edit_iid_col = None

        # Font configuration
        self.style = ttk.Style(self)

        # Select best available sans-serif font
        available_fonts = list(font.families())

        # Preferred fonts in order of preference
        font_preferences = [
            "DejaVu Sans",
            "Liberation Sans",
            "Noto Sans",
            "Ubuntu",
            "Cantarell",
            "FreeSans",
            "Nimbus Sans",
            "Helvetica",
            "Arial",
            "bitstream charter",  # Fallback for systems without fontconfig
        ]

        chosen_family = None
        for candidate in font_preferences:
            if candidate in available_fonts:
                chosen_family = candidate
                break

        if chosen_family is None:
            # Use system default as last resort
            default_font = font.nametofont("TkDefaultFont")
            chosen_family = default_font.actual("family")

        # Create font objects
        self.font_main = font.Font(family=chosen_family, size=11)
        self.font_bold = font.Font(family=chosen_family, size=11, weight="bold")
        self.font_title = font.Font(family=chosen_family, size=14, weight="bold")

        # Configure ttk styles
        self.style.configure(".", font=(chosen_family, 11))
        self.style.configure("TLabel", font=(chosen_family, 11))
        self.style.configure("TButton", font=(chosen_family, 11))
        self.style.configure("TEntry", font=(chosen_family, 11))
        self.style.configure("TCheckbutton", font=(chosen_family, 11))
        self.style.configure("Treeview", font=(chosen_family, 11), rowheight=26)
        self.style.configure("Treeview.Heading", font=(chosen_family, 11, "bold"))

        # Apply to all tk (non-ttk) widgets
        self.option_add("*Font", (chosen_family, 11))
        self.option_add("*TkDefaultFont", (chosen_family, 11))

        self._build_ui()
        self._rebuild_dynamic_ui_and_tree()

    # =========================
    # UI Setup
    # =========================
    def _build_ui(self):
        # Menu
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        view_menu = tk.Menu(menubar, tearoff=False)
        self.menu_view = view_menu
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Manage columns …", command=self._open_columns_dialog)

        # Title + Logo
        frm_title = ttk.Frame(self, padding=(10, 6))
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

        # Discipline Checkboxes
        frm_disc = ttk.LabelFrame(self, text="Disciplines", padding=(10, 8))
        frm_disc.pack(fill="x", padx=10, pady=(0, 6))

        for idx, d in enumerate(DISCIPLINES):
            cb = ttk.Checkbutton(frm_disc, text=d.label, variable=self.disc_state[d.code],
                                 command=self._on_toggle_disciplines)
            cb.grid(row=0, column=idx, sticky="w", padx=(0, 12))

        # Input Area (Name, Start Number, dynamic discipline entries + buttons)
        frm_input = ttk.Frame(self, padding=(10, 8))
        frm_input.pack(fill="x")

        ttk.Label(frm_input, text="Name:").grid(row=0, column=0, sticky="w")
        self.ent_name = ttk.Entry(frm_input, width=20)
        self.ent_name.grid(row=0, column=1, sticky="w", padx=(6, 12))

        ttk.Label(frm_input, text="Start Number:").grid(row=0, column=2, sticky="w")
        self.ent_startnr = ttk.Entry(frm_input, width=10)
        self.ent_startnr.grid(row=0, column=3, sticky="w", padx=(6, 12))

        # Container for dynamic discipline fields
        self.frm_dyn_inputs = ttk.Frame(frm_input)
        self.frm_dyn_inputs.grid(row=0, column=4, sticky="w")

        # Move buttons to their own frame
        frm_buttons = ttk.Frame(frm_input)
        frm_buttons.grid(row=1, column=0, columnspan=105, sticky="w", pady=(8, 0))

        self.btn_add = ttk.Button(frm_buttons, text="Add line", command=self.on_add_row)
        self.btn_add.grid(row=0, column=0, padx=(0, 12))
        
        ttk.Button(frm_buttons, text="save CSV", command=self.export_csv).grid(row=0, column=1, padx=(0, 12))
        ttk.Button(frm_buttons, text="save PDF", command=self.export_pdf).grid(row=0, column=2, padx=(0, 12))
        ttk.Button(frm_buttons, text="Overall awards (PDF/DOCX)", command=self.export_individual_reports).grid(row=0, column=3, padx=(0, 12))

        # Scorsheet options in seperate frame
        frm_scoresheet = ttk.LabelFrame(self, text="Scoresheet", padding=(10, 8))
        frm_scoresheet.pack(fill="x", padx=10, pady=(0, 6))
        # frm_scoresheet.grid(row=2, column=0, columnspan=105, sticky="w", pady=(8, 0))

        ttk.Label(frm_scoresheet, text="Number of circles:").grid(row=0, column=2, sticky="w")
        self.ent_circle = ttk.Entry(frm_scoresheet, width=10)
        self.ent_circle.grid(row=0, column=3, sticky="w", padx=(6, 12))
        self.ent_circle.insert(0, "2")

        # Dropdown für Event
        ttk.Label(frm_scoresheet, text="Event:").grid(row=0, column=4, sticky="w", padx=(20, 6))

        self.event_var = tk.StringVar()
        self.event_var.set(EVENTS[0])  # Standardwert = erstes Element ("ACC")

        self.event_dropdown = ttk.OptionMenu(
            frm_scoresheet,
            self.event_var,
            self.event_var.get(),
            *EVENTS
        )
        self.event_dropdown.grid(row=0, column=5, sticky="w")
        # scoresheet_event = self.event_var.get()

        # Dropdown für Sortierung
        ttk.Label(frm_scoresheet, text="Sorted by").grid(row=0, column=6, sticky="w", padx=(20, 6))

        self.sheetsort_var = tk.StringVar()
        self.sheetsort_var.set(SORTED[0])  # Standardwert = erstes Element ("ACC")

        self.event_dropdown = ttk.OptionMenu(
            frm_scoresheet,
            self.sheetsort_var,
            self.sheetsort_var.get(),
            *SORTED
        )
        self.event_dropdown.grid(row=0, column=7, sticky="w")
        self.btn_add = ttk.Button(frm_scoresheet, text="print scoresheets", command=self.export_scoresheet)
        self.btn_add.grid(row=0, column=8, padx=(0, 12))


        for c in range(103):
            frm_input.grid_columnconfigure(c, weight=0)
        frm_input.grid_columnconfigure(103, weight=1)

        # Table (built dynamically)
        self.frm_table = ttk.Frame(self, padding=(10, 6))
        self.frm_table.pack(fill="both", expand=True)

    # =========================
    # Choose Logo
    # =========================
    def on_choose_logo(self):
        path = filedialog.askopenfilename(
            title="Select Logo File",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("All files", "*.*")],
        )
        if not path:
            return
        self.competition.logo_path = path
        self.lbl_logo_name.config(text=os.path.basename(path))

    # =========================
    # Toggle Disciplines
    # =========================
    def _on_toggle_disciplines(self):
        # Update active disciplines in service
        active = {d.code for d in DISCIPLINES if self.disc_state[d.code].get()}
        self.service.set_active_disciplines(active)

        # Rebuild UI and table, recalculate ranks/total
        self._rebuild_dynamic_ui_and_tree()

    # =========================
    # Rebuild Dynamic UI & Tree
    # =========================
    def _rebuild_dynamic_ui_and_tree(self):
        # 1) Re-create dynamic entry fields
        for w in self.frm_dyn_inputs.winfo_children():
            w.destroy()
        self.disc_entries.clear()

        col = 0
        for d in DISCIPLINES:
            if self.disc_state[d.code].get():
                ttk.Label(self.frm_dyn_inputs, text=f"{d.label} (Res):").grid(row=0, column=col, sticky="w", padx=(0, 4))
                ent = ttk.Entry(self.frm_dyn_inputs, width=8)
                ent.grid(row=0, column=col+1, sticky="w", padx=(0, 12))
                self.disc_entries[d.code] = ent
                col += 2

        # 2) Rebuild table (columns depend on active disciplines)
        #    We destroy/re-create Treeview, preserving order & data.
        old_children = []
        if self.tree is not None:
            old_children = list(self.tree.get_children(""))
            # Remember order
        for w in self.frm_table.winfo_children():
            w.destroy()
        self._build_tree()

        # 3) Re-insert existing data
        for iid in self.data.keys():
            # Create item in tree, then update values
            self.tree.insert("", "end", iid=iid, values=[""] * len(self.all_columns))
            self._update_tree_row(iid)

        # Rankings are already updated by service.set_active_disciplines()

    # =========================
    # Create Tree Dynamically
    # =========================
    def _build_tree(self):
        # Assemble columns
        self.all_columns = []
        self.column_headers = {}
        self.column_widths = {}
        self.column_anchors = {}
        self.numeric_columns = set()

        # Base Columns
        base_defs = [
            ("name", "Name", 200, "w", False),
            ("startnumber", "Start No.", 80, "center", True),
            ("total", "Total Points", 120, "center", True),
            ("overall_rank", "Overall Rank", 100, "center", True),
        ]
        for key, hdr, w, anc, isnum in base_defs:
            self.all_columns.append(key)
            self.column_headers[key] = hdr
            self.column_widths[key] = w
            self.column_anchors[key] = anc
            if isnum:
                self.numeric_columns.add(key)

        # Discipline Columns (only active)
        for d in DISCIPLINES:
            if not self.disc_state[d.code].get():
                continue
            # Result
            key_e = f"{d.code}_res"
            self.all_columns.append(key_e)
            self.column_headers[key_e] = f"{d.label} Res"
            self.column_widths[key_e] = 90
            self.column_anchors[key_e] = "center"
            self.numeric_columns.add(key_e)
            # Points
            key_p = f"{d.code}_pts"
            self.all_columns.append(key_p)
            self.column_headers[key_p] = f"{d.label} Pts"
            self.column_widths[key_p] = 90
            self.column_anchors[key_p] = "center"
            self.numeric_columns.add(key_p)
            # Rank
            key_r = f"{d.code}_rank"
            self.all_columns.append(key_r)
            self.column_headers[key_r] = f"{d.label} Rank"
            self.column_widths[key_r] = 80
            self.column_anchors[key_r] = "center"
            self.numeric_columns.add(key_r)

        # Initialize/preserve visibility
        new_visibility = {}
        for key in self.all_columns:
            # Preserve known setting, otherwise default visible
            new_visibility[key] = self.column_visibility.get(key, True)
        self.column_visibility = new_visibility
        self.display_columns = [c for c in self.all_columns if self.column_visibility.get(c, True)]

        # Tree + Scrollbar
        self.tree = ttk.Treeview(
            self.frm_table,
            columns=self.all_columns,
            show="headings",
            selectmode="browse",
            height=20,
            displaycolumns=self.display_columns,
        )
        yscroll = ttk.Scrollbar(self.frm_table, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(self.frm_table, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscroll=xscroll.set)
        self.tree.pack(side="bottom", fill="both", expand=True)
        xscroll.pack(side="bottom", fill="x")

        # Spalten konfigurieren
        for col in self.all_columns:
            self.tree.heading(col, text=self.column_headers[col], command=lambda c=col: self.on_sort_column(c))
            self.tree.column(col, width=self.column_widths[col], anchor=self.column_anchors[col], stretch=False)

        # Events: Inline-Edit
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.bind("<Return>", self._commit_inline_edit)
        self.bind("<KP_Enter>", self._commit_inline_edit)
        self.bind("<Escape>", self._cancel_inline_edit)

    # =========================
    # Column Dialog (show/hide)
    # =========================
    def _open_columns_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Show/Hide Columns")
        dlg.transient(self)
        dlg.grab_set()
        frm = ttk.Frame(dlg, padding=10)
        frm.pack(fill="both", expand=True)

        vars_map = {}
        row = 0
        ttk.Label(frm, text="Visible Columns (only currently available):", font=self.font_bold).grid(row=row, column=0, sticky="w")
        row += 1
        for col in self.all_columns:
            v = tk.BooleanVar(value=self.column_visibility.get(col, True))
            vars_map[col] = v
            cb = ttk.Checkbutton(frm, text=self.column_headers[col], variable=v)
            cb.grid(row=row, column=0, sticky="w")
            row += 1

        btns = ttk.Frame(frm)
        btns.grid(row=row, column=0, pady=(8, 0), sticky="e")
        ttk.Button(btns, text="Cancel", command=dlg.destroy).pack(side="right", padx=(6, 0))
        def apply_and_close():
            # Apply visibility
            for col, v in vars_map.items():
                self.column_visibility[col] = bool(v.get())
            self.display_columns = [c for c in self.all_columns if self.column_visibility.get(c, True)]
            try:
                self.tree["displaycolumns"] = self.display_columns
            except Exception:
                pass
            dlg.destroy()
        ttk.Button(btns, text="Apply", command=apply_and_close).pack(side="right")

    # =========================
    # Parser/Formatter
    # =========================
    def _parse_float(self, s, allow_empty=True):
        s = (s or "").strip()
        if s == "":
            return None if allow_empty else 0.0
        return float(s.replace(",", "."))

    def _parse_int(self, s, allow_empty=True):
        s = (s or "").strip()
        if s == "":
            return None if allow_empty else 0
        return int(s)

    def _format_number(self, v):
        if v is None:
            return ""
        try:
            f = float(v)
        except (TypeError, ValueError):
            return str(v)
        if abs(f - int(f)) < 1e-9:
            return str(int(f))
        return f"{f:.2f}"

    def _next_free_startnr(self):
        used = {int(r.get("startnumber")) for r in self.data.values() if r.get("startnumber") is not None}
        n = 1
        while n in used:
            n += 1
        return n

    # =========================
    # Add Row
    # =========================
    def on_add_row(self):
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

        # Capture values per active discipline
        disc_values = {}
        for d in DISCIPLINES:
            ent = self.disc_entries.get(d.code)
            if ent is None:
                disc_values[d.code] = 0.0
            else:
                try:
                    v = self._parse_float(ent.get())
                    disc_values[d.code] = v if v is not None else 0.0
                except ValueError:
                    messagebox.showwarning("Invalid Input", f"{d.label}: Result must be a number.")
                    return

        # Use service to add participant
        iid = self.tree.insert("", "end", values=[""] * len(self.all_columns))
        try:
            self.service.add_participant(iid, name, startnr, disc_values)
            self._update_tree_row(iid)

            # Update all rows to refresh ranks
            for pid in self.data.keys():
                self._update_tree_row(pid)
        except ValueError as e:
            self.tree.delete(iid)
            messagebox.showerror("Error", str(e))
            return

        # Clear inputs (name may remain)
        self.ent_startnr.delete(0, "end")
        for ent in self.disc_entries.values():
            ent.delete(0, "end")

    # =========================
    # Row Display
    # =========================
    def _update_tree_row(self, iid):
        row = self.data[iid]
        values = []
        for col in self.all_columns:
            if col in ("name",):
                values.append(row["name"])
            elif col in ("startnumber", "total", "overall_rank"):
                values.append(self._format_number(row.get(col)))
            elif col.endswith("_res") or col.endswith("_pts") or col.endswith("_rank"):
                values.append(self._format_number(row.get(col)))
            else:
                values.append("")
        self.tree.item(iid, values=values)

    # =========================
    # Inline-Editing
    # =========================
    def on_tree_double_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        rowid = self.tree.identify_row(event.y)
        colid = self.tree.identify_column(event.x)  # '#1', '#2', ...
        if not rowid or not colid:
            return

        col_index = int(colid.replace("#", "")) - 1
        col_key = self.tree["displaycolumns"][col_index]  # visible column
        # Editable: name, startnumber, *_res (of active ones!)
        editable = {"name", "startnumber"}
        for d in DISCIPLINES:
            if self.disc_state[d.code].get():
                editable.add(f"{d.code}_res")

        if col_key not in editable:
            return

        bbox = self.tree.bbox(rowid, colid)
        if not bbox:
            return
        x, y, w, h = bbox

        current_text = self.tree.item(rowid, "values")[col_index]

        self._cancel_inline_edit()
        self._edit_entry = ttk.Entry(self.tree)
        self._edit_entry.insert(0, current_text)
        self._edit_entry.select_range(0, "end")
        self._edit_entry.focus_set()
        self._edit_entry.place(x=x, y=y, width=w, height=h)
        self._edit_iid_col = (rowid, col_key)
        self._edit_entry.bind("<FocusOut>", self._commit_inline_edit)

    def _commit_inline_edit(self, event=None):
        if not self._edit_entry or not self._edit_iid_col:
            return
        iid, col_key = self._edit_iid_col
        new_text = self._edit_entry.get()
        self._edit_entry.destroy()
        self._edit_entry = None
        self._edit_iid_col = None

        # Validate & apply using service
        try:
            if col_key == "name":
                if new_text.strip() == "":
                    messagebox.showwarning("Invalid Name", "The name cannot be empty.")
                    return
                self.service.update_participant_name(iid, new_text.strip())
                self._update_tree_row(iid)
                return

            if col_key == "startnumber":
                try:
                    new_sn = int(new_text)
                except ValueError:
                    messagebox.showwarning("Invalid Start Number", "The start number must be an integer.")
                    return
                self.service.update_participant_startnumber(iid, new_sn)
                self._update_tree_row(iid)
                return

            # Discipline result?
            if col_key.endswith("_res"):
                try:
                    new_val = self._parse_float(new_text, allow_empty=False)
                except ValueError:
                    messagebox.showwarning("Invalid Input", "Please enter a number.")
                    return
                disc_code = col_key[:-4]
                self.service.update_participant_result(iid, disc_code, float(new_val))

                # Update all rows to refresh ranks
                for pid in self.data.keys():
                    self._update_tree_row(pid)
                return
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

    def _cancel_inline_edit(self, event=None):
        if self._edit_entry:
            self._edit_entry.destroy()
        self._edit_entry = None
        self._edit_iid_col = None

    # =========================
    # Sorting
    # =========================
    def _is_numeric_column(self, key):
        return key in self.numeric_columns

    def on_sort_column(self, col):
        asc = self.sort_state.get(col, True)
        asc = not asc
        self.sort_state[col] = asc
        self._apply_sort(col, asc)
        self._last_sort_col = col

    def _apply_sort(self, col, ascending=True):
        children = list(self.tree.get_children(""))

        def get_val(iid):
            row = self.data.get(iid, {})
            v = row.get(col)
            if v is None and col in ("name",):
                return str(row.get("name") or "")
            if v is None:
                try:
                    idx = self.tree["displaycolumns"].index(col)
                    val = self.tree.item(iid, "values")[idx]
                except Exception:
                    val = ""
                if self._is_numeric_column(col):
                    try:
                        return float(str(val).replace(",", "."))
                    except ValueError:
                        return float("-inf")
                return str(val)
            if self._is_numeric_column(col):
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return float("-inf")
            return str(v)

        sorted_children = sorted(children, key=get_val, reverse=not ascending)
        for idx, iid in enumerate(sorted_children):
            self.tree.move(iid, "", idx)

    # =========================
    # Export CSV
    # =========================
    def export_csv(self):
        filename = filedialog.asksaveasfilename(
            title="Save CSV",
            defaultextension=".csv",
            filetypes=[("CSV file", "*.csv")]
        )
        if not filename:
            return

        try:
            # Get visible columns and participant order from GUI
            cols = list(self.tree["displaycolumns"])
            participant_order = list(self.tree.get_children())

            # Use export service
            self.export_service.export_csv(filename, cols, self.column_headers, participant_order)
            messagebox.showinfo("Export Successful", f"The CSV has been saved:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred:\n{e}")

    # =========================
    # Export PDF Full List
    # =========================
    def export_pdf(self):
        filename = filedialog.asksaveasfilename(
            title="Save PDF",
            defaultextension=".pdf",
            filetypes=[("PDF file", "*.pdf")]
        )
        if not filename:
            return

        try:
            participant_order = list(self.tree.get_children())
            self.export_service.export_pdf_full_list(filename, participant_order)
            messagebox.showinfo("Export Successful", f"The PDF has been saved:\n{filename}")
        except Exception as e:
            messagebox.showerror("PDF Error", f"An error occurred while creating the PDF:\n{e}")

    # =========================
    def export_individual_reports(self):
        if not self.data:
            messagebox.showwarning("No Data", "There are no participants.")
            return

        out_file = filedialog.asksaveasfilename(
            title="Save Report",
            defaultextension=".pdf",
            filetypes=[
                ("PDF File", "*.pdf"),
                ("Word Document", "*.docx")
            ]
        )
        if not out_file:
            return

        try:
            # Sort by overall rank
            participant_order = sorted(
                self.data.keys(),
                key=lambda pid: (self.data[pid].get("overall_rank") or 10**9, self.data[pid].get("name") or "")
            )

            self.export_service.export_individual_reports(
                out_file,
                participant_order,
                self.competition.logo_path
            )
            messagebox.showinfo("Export Successful", f"Report saved:\n{out_file}")
        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred:\n{e}")

    # Export: Individual Reports (A4, compact discipline table, logo)
    # =========================
    def export_scoresheet(self):
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.units import mm
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
        except Exception:
            messagebox.showerror(
                "ReportLab fehlt",
                "Für den PDF-Export wird das Paket 'reportlab' benötigt.\n"
                "Installiere es mit:\n\n    pip install reportlab"
            )
            return

        filename = filedialog.asksaveasfilename(
            title="PDF speichern",
            defaultextension=".pdf",
            filetypes=[("PDF-Datei", "*.pdf")]
        )
        if not filename:
            return

        doc = SimpleDocTemplate(
            filename,
            pagesize=landscape(A4),
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

        styles = getSampleStyleSheet()
        story = []

        title_text = self.ent_title.get().strip() or "Wettbewerb"
        story.append(Paragraph(title_text, styles["Title"]))
        story.append(Spacer(1, 6))

        # Tabelle: Basis + aktive Disziplinspalten (Erg/Pkt/Rang)
        headers = headers = ["startnr", "Name", "Wurf 1", "Wurf 2", "Wurf 3", "Wurf 4", "Wurf 5", "Gesamt"]
        col_keys = ["startnummer", "name", "gesamt", "gesamtrang"]
        for d in DISCIPLINES:
            if self.disc_state[d.code].get():
                headers += [f"{d.label} Erg", f"{d.label} Pkt", f"{d.label} Rang"]
                col_keys += [f"{d.code}_erg", f"{d.code}_pkt", f"{d.code}_rang"]

        data_rows = []
        for iid in self.tree.get_children():
            r = self.data[iid]
            row_vals = []
            for k in col_keys:
                if k == "name":
                    row_vals.append(str(r["name"]))
                else:
                    row_vals.append(self._format_number(r.get(k)))
            data_rows.append(row_vals)

        table_data = [headers] + data_rows

        # Spaltenbreiten heuristisch
        # Basis: 60 + 18 + 22 + 24 = 124mm, Rest auf Disziplinen; pro Disziplin ~ (22+22+20)=64mm
        col_widths = []
        base_widths = [45 * mm, 11 * mm, 11 * mm, 11 * mm]
        col_widths.extend(base_widths)
        for d in DISCIPLINES:
            if self.disc_state[d.code].get():
                col_widths.extend([11 * mm, 11 * mm, 9 * mm])

        tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 5),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),

            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 6),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("ALIGN", (0, 1), (0, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ]))
        story.append(tbl)

        try:
            doc.build(story)
        except Exception as e:
            messagebox.showerror("PDF Error", f"An error occurred while creating the PDF:\n{e}")
            return
        messagebox.showinfo("Export Successful", f"The PDF has been saved:\n{filename}")

    # =========================
    # Header/Start/Helper Functions
    # =========================
    def _is_active(self, code):
        return bool(self.disc_state[code].get())


# ==============================
# Discipline Configuration
# ==============================
DISCIPLINES = [
    ACC,
    AUS,
    MTA,
    END,
    FC,
    TC,
    TIMED,
]

# ==============================
# Starting Point
# ==============================
if __name__ == "__main__":
    app = ScoreTableApp()
    app.mainloop()
