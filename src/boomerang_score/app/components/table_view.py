"""Table view component for displaying participants and their scores."""

from typing import Callable, Any, Dict
import tkinter as tk
from tkinter import ttk, font as tkfont


class ParticipantTableView:
    """
    TreeView widget with sorting and inline editing capabilities.

    Displays participants with base columns (Name, Start No., Total Points, Overall Rank)
    and dynamic discipline columns (Result, Points, Rank per active discipline).
    """

    def __init__(
        self,
        parent: tk.Widget,
        disciplines: list,
        disc_state: Dict[str, tk.BooleanVar],
        competition: Any,
        service: Any,
        fonts: Dict[str, tkfont.Font],
        grouped_headers: bool = True,
    ) -> None:
        """
        Initialize the participant table view.

        Args:
            parent: Parent widget
            disciplines: List of Discipline objects
            disc_state: Dict of discipline code -> BooleanVar for active state
            competition: Competition instance
            service: CompetitionService instance
            fonts: Dict with 'main' and 'bold' fonts
            grouped_headers: If True, show a discipline group row above sub-columns.
                             If False, use a single header row with full column names.
        """
        self.parent = parent
        self.disciplines = disciplines
        self.disc_state = disc_state
        self.competition = competition
        self.service = service
        self.fonts = fonts
        self.grouped_headers = grouped_headers

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

        # Grouped header canvas
        self._header_canvas = None

        # Inline editing state
        self._edit_entry = None
        self._edit_iid_col = None

        # Callbacks
        self._on_data_changed = None

        # Tree widget (will be created by rebuild)
        self.tree = None
        self.frame = ttk.Frame(parent)

    def build(self) -> None:
        """Build or rebuild the tree widget with current active disciplines."""
        # Clear old widgets
        if self._header_canvas:
            self._header_canvas.destroy()
            self._header_canvas = None
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
            ("name", "Name", 190, "w", False),
            ("startnumber", "Start No.", 60, "center", True),
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
            if self.grouped_headers:
                self.column_headers[key_e] = "Res"
                self.column_widths[key_e] = 60
            else:
                self.column_headers[key_e] = f"{d.label} Res"
                self.column_widths[key_e] = 90
            self.column_anchors[key_e] = "center"
            self.numeric_columns.add(key_e)
            # Points
            key_p = f"{d.code}_pts"
            self.all_columns.append(key_p)
            if self.grouped_headers:
                self.column_headers[key_p] = "Pts"
                self.column_widths[key_p] = 60
            else:
                self.column_headers[key_p] = f"{d.label} Pts"
                self.column_widths[key_p] = 90
            self.column_anchors[key_p] = "center"
            self.numeric_columns.add(key_p)
            # Rank
            key_r = f"{d.code}_rank"
            self.all_columns.append(key_r)
            if self.grouped_headers:
                self.column_headers[key_r] = "Rnk"
                self.column_widths[key_r] = 55
            else:
                self.column_headers[key_r] = f"{d.label} Rank"
                self.column_widths[key_r] = 80
            self.column_anchors[key_r] = "center"
            self.numeric_columns.add(key_r)

        # Initialize/preserve visibility
        new_visibility = {}
        for key in self.all_columns:
            new_visibility[key] = self.column_visibility.get(key, True)
        self.column_visibility = new_visibility
        self.display_columns = [
            c for c in self.all_columns if self.column_visibility.get(c, True)
        ]

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
        self.tree.configure(yscrollcommand=yscroll.set)

        # Pack tree and scrollbar; grouped header is inserted above tree afterwards
        yscroll.pack(side="right", fill="y")
        self.tree.pack(side="top", fill="both", expand=True)
        if self.grouped_headers:
            self._build_custom_header()

        # Configure columns
        for col in self.all_columns:
            self.tree.heading(
                col,
                text=self.column_headers[col],
                command=lambda c=col: self.on_sort_column(c),
            )
            self.tree.column(
                col,
                width=self.column_widths[col],
                anchor=self.column_anchors[col],
                stretch=False,
            )

        # Bind inline editing events
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<Button-3>", self._on_right_click)
        self.tree.bind("<Button-2>", self._on_right_click)  # For macOS

    def _build_custom_header(self) -> None:
        """Draw a grouped header row above the Treeview for discipline columns."""
        if self._header_canvas:
            self._header_canvas.destroy()
            self._header_canvas = None

        # Compute x position of each visible column (left edge)
        x_pos = {}
        x = 0
        for col in self.all_columns:
            if self.column_visibility.get(col, True):
                x_pos[col] = x
                x += self.column_widths[col]

        # Collect discipline groups that have at least one visible sub-column
        groups = []
        for d in self.disciplines:
            if not self.disc_state[d.code].get():
                continue
            disc_cols = [f"{d.code}_res", f"{d.code}_pts", f"{d.code}_rank"]
            visible = [c for c in disc_cols if c in x_pos]
            if not visible:
                continue
            x_start = x_pos[visible[0]]
            x_end = x_pos[visible[-1]] + self.column_widths[visible[-1]]
            groups.append((x_start, x_end, d.label))

        if not groups:
            return

        style = ttk.Style()
        bg = style.lookup("Treeview.Heading", "background") or "#e1e1e1"
        fg = style.lookup("Treeview.Heading", "foreground") or "#000000"
        if not bg:
            bg = "#e1e1e1"
        if not fg:
            fg = "#000000"

        height = 22
        self._header_canvas = tk.Canvas(
            self.frame, height=height, bg=bg, highlightthickness=0, bd=0
        )
        self._header_canvas.pack(side="top", fill="x", before=self.tree)

        for x_start, x_end, label in groups:
            mid_x = (x_start + x_end) // 2
            self._header_canvas.create_rectangle(
                x_start + 1,
                1,
                x_end - 1,
                height - 1,
                outline="#a0a0a0",
                fill=bg,
            )
            self._header_canvas.create_text(
                mid_x,
                height // 2,
                text=label,
                fill=fg,
                font=self.fonts["bold"],
            )

    def toggle_grouped_headers(self) -> None:
        """Switch between grouped and flat header mode and rebuild the table."""
        self.grouped_headers = not self.grouped_headers
        self.build()
        self.refresh_from_data()

    def pack(self, **kwargs) -> None:
        """Pack the table frame."""
        self.frame.pack(**kwargs)

    def set_data_changed_callback(self, callback: Callable[[], None]) -> None:
        """Set callback to be called when data changes."""
        self._on_data_changed = callback

    def _notify_data_changed(self) -> None:
        """Notify that data has changed."""
        if self._on_data_changed:
            self._on_data_changed()

    def refresh_from_data(self) -> None:
        """Refresh the whole table from current data."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for startnr in self.competition.participants:
            self.tree.insert(
                "", "end", iid=str(startnr), values=[""] * len(self.all_columns)
            )
            self.update_row(str(startnr))

        self._notify_data_changed()

    def update_row(self, iid: str) -> None:
        """Update display of a single row (iid is string startnumber)."""
        p = self.competition.participants[int(iid)]
        values = []
        for col in self.all_columns:
            if col == "name":
                values.append(p.name)
            elif col == "startnumber":
                values.append(self._format_number(p.startnumber))
            elif col == "total":
                values.append(self._format_number(p.total_points))
            elif col == "overall_rank":
                values.append(self._format_number(p.overall_rank))
            elif col.endswith("_res"):
                values.append(self._format_number(p.get_result(col[:-4])))
            elif col.endswith("_pts"):
                values.append(self._format_number(p.get_points(col[:-4])))
            elif col.endswith("_rank"):
                values.append(self._format_number(p.get_rank(col[:-5])))
            else:
                values.append("")
        self.tree.item(iid, values=values)

    def update_all_rows(self) -> None:
        """Update display of all rows."""
        for startnr in self.competition.participants:
            self.update_row(str(startnr))

    def insert_row(self, values):
        """Insert a new row and return its ID."""
        return self.tree.insert("", "end", values=values)

    def delete_row(self, iid):
        """Delete a row."""
        self.tree.delete(iid)

    def _on_right_click(self, event):
        """Show context menu on right-click."""
        item = self.tree.identify_row(event.y)
        if not item:
            return

        # Select the item
        self.tree.selection_set(item)

        # Create context menu
        menu = tk.Menu(self.tree, tearoff=0)
        menu.add_command(
            label="Delete line", command=lambda: self._on_delete_selected()
        )
        menu.post(event.x_root, event.y_root)

    def _on_delete_selected(self):
        """Delete the selected participant."""
        selection = self.tree.selection()
        if not selection:
            return

        iid = selection[0]
        startnr = int(iid)

        from tkinter import messagebox

        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete participant '{self.competition.participants[startnr].name}' (Start No. {startnr})?",
        ):
            return

        try:
            # Delete from service
            self.service.delete_participant(startnr)

            # Delete from tree
            self.delete_row(iid)

            # Update all other rows (to refresh ranks)
            self.update_all_rows()
            self._notify_data_changed()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete participant:\n{e}")

    def open_columns_dialog(self, root):
        """Open dialog to show/hide columns."""
        dlg = tk.Toplevel(root)
        dlg.title("Show/Hide Columns")
        dlg.transient(root)
        dlg.grab_set()
        frm = ttk.Frame(dlg, padding=10)
        frm.pack(fill="both", expand=True)

        # Build a human-readable label for each column (discipline sub-columns need prefix)
        disc_label_map = {d.code: d.label for d in self.disciplines}

        def _col_display_name(col):
            for suffix, name in (("_res", "Res"), ("_pts", "Pts"), ("_rank", "Rank")):
                if col.endswith(suffix):
                    code = col[: -len(suffix)]
                    label = disc_label_map.get(code, code.upper())
                    return f"{label} {name}"
            return self.column_headers[col]

        vars_map = {}
        row = 0
        ttk.Label(
            frm,
            text="Visible Columns (only currently available):",
            font=self.fonts["bold"],
        ).grid(row=row, column=0, sticky="w")
        row += 1
        for col in self.all_columns:
            v = tk.BooleanVar(value=self.column_visibility.get(col, True))
            vars_map[col] = v
            cb = ttk.Checkbutton(frm, text=_col_display_name(col), variable=v)
            cb.grid(row=row, column=0, sticky="w")
            row += 1

        btns = ttk.Frame(frm)
        btns.grid(row=row, column=0, pady=(8, 0), sticky="e")
        ttk.Button(btns, text="Cancel", command=dlg.destroy).pack(
            side="right", padx=(6, 0)
        )

        def apply_and_close():
            for col, v in vars_map.items():
                self.column_visibility[col] = bool(v.get())
            self.display_columns = [
                c for c in self.all_columns if self.column_visibility.get(c, True)
            ]
            try:
                self.tree["displaycolumns"] = self.display_columns
            except Exception:
                pass
            if self.grouped_headers:
                self._build_custom_header()
            dlg.destroy()

        ttk.Button(btns, text="Apply", command=apply_and_close).pack(side="right")

    def on_tree_double_click(self, event):
        """Handle double-click for inline editing."""
        # Commit any existing edit before starting a new one
        if self._edit_entry:
            self.commit_inline_edit()

        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        rowid = self.tree.identify_row(event.y)
        colid = self.tree.identify_column(event.x)
        if not rowid or not colid:
            return

        col_index = int(colid.replace("#", "")) - 1
        col_key = self.tree["displaycolumns"][col_index]

        # Editable columns: name, startnumber, and *_res for active disciplines
        editable = {"name", "startnumber"}
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
        self._edit_entry = ttk.Entry(self.tree, font=self.fonts["main"])
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
                new_startnr = self._parse_int(new_value)
                if new_startnr is None:
                    raise ValueError("Startnumber must be an integer")
                if new_startnr == startnr:
                    self.cancel_inline_edit()
                    return
                self.service.change_startnumber(startnr, new_startnr)
                # After startnumber change, we need to rebuild the row with new IID
                # It's easiest to just refresh the whole table data display
                self.refresh_from_data()
                self.cancel_inline_edit()
                return
            elif col_key.endswith("_res"):
                disc_code = col_key.replace(
                    "_res", ""
                )  # Already lowercase (e.g., "acc_res" -> "acc")
                v = self._parse_float(new_value)
                self.service.update_participant_result(
                    startnr, disc_code, v if v is not None else 0.0
                )

            # Update all rows to refresh calculated values
            self.update_all_rows()
            self._notify_data_changed()

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

        def get_val(startnr):
            p = self.competition.participants[startnr]
            if col == "name":
                v = p.name
            elif col == "startnumber":
                v = p.startnumber
            elif col == "total":
                v = p.total_points
            elif col == "overall_rank":
                v = p.overall_rank
            elif col.endswith("_res"):
                v = p.get_result(col[:-4])
            elif col.endswith("_pts"):
                v = p.get_points(col[:-4])
            elif col.endswith("_rank"):
                v = p.get_rank(col[:-5])
            else:
                v = None
            if v is None:
                return (1, 0) if ascending else (0, float("inf"))
            if col in self.numeric_columns:
                try:
                    return (0, float(v))
                except (ValueError, TypeError):
                    return (1, 0) if ascending else (0, float("inf"))
            return (0, str(v))

        items = [
            (startnr, get_val(startnr)) for startnr in self.competition.participants
        ]
        items.sort(key=lambda x: x[1], reverse=not ascending)

        for index, (startnr, _) in enumerate(items):
            self.tree.move(str(startnr), "", index)

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
