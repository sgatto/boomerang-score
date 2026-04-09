"""Table view component for displaying participants and their scores."""

from typing import Optional, Callable, Any, Dict
import tkinter as tk
from tkinter import ttk, font as tkfont


class ParticipantTableView:
    """
    TreeView widget with sorting and inline editing capabilities.

    Displays participants with base columns (Name, Start No., Total Points, Overall Rank)
    and dynamic discipline columns (Result, Points, Rank per active discipline).
    """

    def __init__(self, parent: tk.Widget, disciplines: list, disc_state: Dict[str, tk.BooleanVar],
                 data: Any, service: Any, fonts: Dict[str, tkfont.Font]) -> None:
        """
        Initialize the participant table view.

        Args:
            parent: Parent widget
            disciplines: List of Discipline objects
            disc_state: Dict of discipline code -> BooleanVar for active state
            data: LegacyDataAdapter for participant data
            service: CompetitionService instance
            fonts: Dict with 'main' and 'bold' fonts
        """
        self.parent = parent
        self.disciplines = disciplines
        self.disc_state = disc_state
        self.data = data
        self.service = service
        self.fonts = fonts

        # Column management
        self.all_columns = []
        self.display_columns = []
        self.column_headers = {}
        self.column_widths = {}
        self.column_anchors = {}
        self.column_visibility = {}
        self.numeric_columns = set()

        # Sorting state
        self.sort_state = {}

        # Inline editing state
        self._edit_entry = None
        self._edit_iid_col = None

        # Tree widget (will be created by rebuild)
        self.tree = None
        self.frame = ttk.Frame(parent)

    def build(self) -> None:
        """Build or rebuild the tree widget with current active disciplines."""
        # Clear old tree if exists
        if self.tree:
            self.tree.destroy()

        # Assemble columns
        self.all_columns = []
        self.column_headers = {}
        self.column_widths = {}
        self.column_anchors = {}
        self.numeric_columns = set()

        # Base columns
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

        # Discipline columns (only active)
        for d in self.disciplines:
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
            new_visibility[key] = self.column_visibility.get(key, True)
        self.column_visibility = new_visibility
        self.display_columns = [c for c in self.all_columns if self.column_visibility.get(c, True)]

        # Create tree widget
        self.tree = ttk.Treeview(
            self.frame,
            columns=self.all_columns,
            show="headings",
            selectmode="browse",
            height=20,
            displaycolumns=self.display_columns,
        )

        # Scrollbars
        yscroll = ttk.Scrollbar(self.frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(self.frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        # Pack tree and scrollbars
        yscroll.pack(side="right", fill="y")
        self.tree.pack(side="top", fill="both", expand=True)
        xscroll.pack(side="bottom", fill="x")

        # Configure columns
        for col in self.all_columns:
            self.tree.heading(col, text=self.column_headers[col],
                            command=lambda c=col: self.on_sort_column(c))
            self.tree.column(col, width=self.column_widths[col],
                           anchor=self.column_anchors[col], stretch=False)

        # Bind inline editing events
        self.tree.bind("<Double-1>", self.on_tree_double_click)

    def pack(self, **kwargs) -> None:
        """Pack the table frame."""
        self.frame.pack(**kwargs)

    def update_row(self, iid: str) -> None:
        """Update display of a single row (iid is string startnumber)."""
        startnr = int(iid)  # Convert tree ID to startnumber
        row = self.data[startnr]
        values = []
        for col in self.all_columns:
            if col == "name":
                values.append(row["name"])
            elif col in ("startnumber", "total", "overall_rank"):
                values.append(self._format_number(row.get(col)))
            elif col.endswith("_res") or col.endswith("_pts") or col.endswith("_rank"):
                values.append(self._format_number(row.get(col)))
            else:
                values.append("")
        self.tree.item(iid, values=values)

    def update_all_rows(self) -> None:
        """Update display of all rows."""
        for startnr in self.data.keys():
            self.update_row(str(startnr))

    def insert_row(self, values):
        """Insert a new row and return its ID."""
        return self.tree.insert("", "end", values=values)

    def delete_row(self, iid):
        """Delete a row."""
        self.tree.delete(iid)

    def open_columns_dialog(self, root):
        """Open dialog to show/hide columns."""
        dlg = tk.Toplevel(root)
        dlg.title("Show/Hide Columns")
        dlg.transient(root)
        dlg.grab_set()
        frm = ttk.Frame(dlg, padding=10)
        frm.pack(fill="both", expand=True)

        vars_map = {}
        row = 0
        ttk.Label(frm, text="Visible Columns (only currently available):",
                 font=self.fonts['bold']).grid(row=row, column=0, sticky="w")
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
            for col, v in vars_map.items():
                self.column_visibility[col] = bool(v.get())
            self.display_columns = [c for c in self.all_columns if self.column_visibility.get(c, True)]
            try:
                self.tree["displaycolumns"] = self.display_columns
            except Exception:
                pass
            dlg.destroy()

        ttk.Button(btns, text="Apply", command=apply_and_close).pack(side="right")

    def on_tree_double_click(self, event):
        """Handle double-click for inline editing."""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        rowid = self.tree.identify_row(event.y)
        colid = self.tree.identify_column(event.x)
        if not rowid or not colid:
            return

        col_index = int(colid.replace("#", "")) - 1
        col_key = self.tree["displaycolumns"][col_index]

        # Editable columns: name and *_res for active disciplines
        # Note: startnumber is immutable and cannot be edited
        editable = {"name"}
        for d in self.disciplines:
            if self.disc_state[d.code].get():
                editable.add(f"{d.code}_res")

        if col_key not in editable:
            return

        bbox = self.tree.bbox(rowid, colid)
        if not bbox:
            return
        x, y, w, h = bbox

        current_text = self.tree.item(rowid, "values")[col_index]

        # Create entry widget
        self._edit_entry = ttk.Entry(self.tree, font=self.fonts['main'])
        self._edit_entry.insert(0, current_text)
        self._edit_entry.select_range(0, "end")
        self._edit_entry.place(x=x, y=y, width=w, height=h)
        self._edit_entry.focus()

        self._edit_iid_col = (rowid, col_key)

    def commit_inline_edit(self):
        """Commit the current inline edit."""
        if not self._edit_entry or not self._edit_iid_col:
            return

        new_value = self._edit_entry.get().strip()
        iid, col_key = self._edit_iid_col
        startnr = int(iid)  # Convert tree ID to startnumber

        try:
            if col_key == "name":
                if not new_value:
                    raise ValueError("Name cannot be empty")
                self.service.update_participant_name(startnr, new_value)
            elif col_key == "startnumber":
                # Startnumber is immutable, cannot be changed
                from tkinter import messagebox
                messagebox.showinfo("Cannot Edit", "Startnumber cannot be changed after creation")
                self.cancel_inline_edit()
                return
            elif col_key.endswith("_res"):
                disc_code = col_key.replace("_res", "")  # Already lowercase (e.g., "acc_res" -> "acc")
                v = self._parse_float(new_value)
                self.service.update_participant_result(startnr, disc_code, v if v is not None else 0.0)

            # Update all rows to refresh calculated values
            self.update_all_rows()

        except ValueError as e:
            from tkinter import messagebox
            messagebox.showerror("Invalid Input", str(e))

        self.cancel_inline_edit()

    def cancel_inline_edit(self):
        """Cancel the current inline edit."""
        if self._edit_entry:
            self._edit_entry.destroy()
            self._edit_entry = None
        self._edit_iid_col = None

    def on_sort_column(self, col):
        """Handle column header click for sorting."""
        ascending = not self.sort_state.get(col, False)
        self.sort_state[col] = ascending
        self._apply_sort(col, ascending)

    def _apply_sort(self, col, ascending=True):
        """Apply sorting to the tree."""
        def get_val(iid):
            row = self.data[iid]
            v = row.get(col)
            if v is None:
                return (1, 0) if ascending else (0, float('inf'))
            if col in self.numeric_columns:
                try:
                    return (0, float(v))
                except (ValueError, TypeError):
                    return (1, 0) if ascending else (0, float('inf'))
            return (0, str(v))

        items = [(iid, get_val(iid)) for iid in self.data.keys()]
        items.sort(key=lambda x: x[1], reverse=not ascending)

        for index, (iid, _) in enumerate(items):
            self.tree.move(iid, "", index)

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

    def _format_number(self, v):
        """Format number for display."""
        if v is None:
            return ""
        try:
            f = float(v)
        except (TypeError, ValueError):
            return str(v)
        if abs(f - int(f)) < 1e-9:
            return str(int(f))
        return f"{f:.2f}"
