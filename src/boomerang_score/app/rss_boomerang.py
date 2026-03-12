
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
    # Force X11 backend to avoid Wayland-related XCB issues
    os.environ["GDK_BACKEND"] = "x11"
    # Disable Xsynchronize to mitigate some race conditions in XCB
    os.environ["_X11_NO_XSYNCHRONIZE"] = "1"
    # QT_QPA_PLATFORM can also affect systems with mixed toolkits
    os.environ["QT_QPA_PLATFORM"] = "xcb"

from boomerang_score.core.scorer import compute_competition_ranks, DISCIPLINES

import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Only import reportlab when needed
# from reportlab.lib import colors
# ...

# ==============================
# Ranking-Hilfsfunktion
# ==============================


# ==============================
# Disziplin-Konfiguration
# ==============================


# Hilfssets
BASE_COLUMNS = ["name", "startnummer", "gesamt", "gesamtrang"]


# ==============================
# Haupt-App
# ==============================
class ScoreTableApp(tk.Tk):
    """
    Dynamische Wettbewerbsliste mit Disziplin-Auswahl:
      - Basis: Name | Startnummer | Gesamtpunkte | Gesamtrang
      - je aktive Disziplin: ERG_[XX] | PKT_[XX] | RANG_[XX]

    - Inline-Edit: Name, Startnummer, und alle aktiven ERG-Werte
    - Sortierung: per Klick, Toggle, numerisch für Zahlen
    - CSV-Export: exportiert die aktuell sichtbaren Spalten (displaycolumns)
    - PDF (Gesamtliste): A4 quer, aktive Disziplinen
    - PDF (Einzelberichte): A4, kompakte Tabelle je Teilnehmer, Logo rechts
    """

    def __init__(self):
        super().__init__()
        self.title("Wertungstabelle – Dynamische Disziplinen")
        self.geometry("1450x720")

        # Datenhaltung: Dict[iid] -> Row-Dict (flat)
        # Felder: "name", "startnummer", "gesamt", "gesamtrang",
        #         für jede Disziplin: "{code}_erg", "{code}_pkt", "{code}_rang"
        self.data = {}

        # Disziplinstatus + Eingabefelder
        self.disc_state = {d.code: tk.BooleanVar(value=d.default_active) for d in DISCIPLINES}
        self.disc_entries = {}  # code -> tk.Entry (Add-Bereich)

        # Tree/Spalten
        self.tree = None
        self.all_columns = []        # komplette Spaltenliste (inkl. unsichtbare)
        self.display_columns = []    # aktuell sichtbare Spalten
        self.column_visibility = {}  # key -> bool
        self.sort_state = {}         # Spalte -> aufsteigend?

        # Inline-Editor
        self._edit_entry = None
        self._edit_iid_col = None

        # Logo + Titel
        self.logo_path = None

        self._build_ui()
        self._rebuild_dynamic_ui_and_tree()

    # =========================
    # UI-Aufbau
    # =========================
    def _build_ui(self):
        # Menü
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        view_menu = tk.Menu(menubar, tearoff=False)
        self.menu_view = view_menu
        menubar.add_cascade(label="Ansicht", menu=view_menu)
        view_menu.add_command(label="Spalten verwalten …", command=self._open_columns_dialog)

        # Titel + Logo
        frm_title = ttk.Frame(self, padding=(10, 6))
        frm_title.pack(fill="x")

        ttk.Label(frm_title, text="Wettbewerbstitel:").grid(row=0, column=0, sticky="w")
        self.ent_title = ttk.Entry(frm_title, width=60)
        self.ent_title.grid(row=0, column=1, sticky="w", padx=(6, 12))
        self.ent_title.insert(0, "Mein Wettbewerb")

        self.lbl_title_display = ttk.Label(frm_title, text="Mein Wettbewerb", font=("Arial", 16, "bold"))
        self.lbl_title_display.grid(row=1, column=0, columnspan=5, sticky="w", pady=(6, 2))

        def update_title(*_):
            self.lbl_title_display.config(text=self.ent_title.get())
        self.ent_title.bind("<KeyRelease>", update_title)

        ttk.Label(frm_title, text="Logo:").grid(row=0, column=2, sticky="e")
        self.lbl_logo_name = ttk.Label(frm_title, text="(kein Logo gewählt)")
        self.lbl_logo_name.grid(row=0, column=3, sticky="w", padx=(6, 6))
        ttk.Button(frm_title, text="Logo wählen…", command=self.on_choose_logo).grid(row=0, column=4, sticky="w")

        # Disziplin-Checkboxen
        frm_disc = ttk.LabelFrame(self, text="Disziplinen", padding=(10, 8))
        frm_disc.pack(fill="x", padx=10, pady=(0, 6))

        for idx, d in enumerate(DISCIPLINES):
            cb = ttk.Checkbutton(frm_disc, text=d.label, variable=self.disc_state[d.code],
                                 command=self._on_toggle_disciplines)
            cb.grid(row=0, column=idx, sticky="w", padx=(0, 12))

        # Eingabe-Bereich (Name, Startnr, dynamische Disziplin-Eingaben + Buttons)
        frm_input = ttk.Frame(self, padding=(10, 8))
        frm_input.pack(fill="x")

        ttk.Label(frm_input, text="Name:").grid(row=0, column=0, sticky="w")
        self.ent_name = ttk.Entry(frm_input, width=20)
        self.ent_name.grid(row=0, column=1, sticky="w", padx=(6, 12))

        ttk.Label(frm_input, text="Startnummer:").grid(row=0, column=2, sticky="w")
        self.ent_startnr = ttk.Entry(frm_input, width=10)
        self.ent_startnr.grid(row=0, column=3, sticky="w", padx=(6, 12))

        # Container für dynamische Disziplin-Eingaben
        self.frm_dyn_inputs = ttk.Frame(frm_input)
        self.frm_dyn_inputs.grid(row=0, column=4, sticky="w")

        # Buttons in eigenes Frame verschieben
        frm_buttons = ttk.Frame(frm_input)
        frm_buttons.grid(row=1, column=0, columnspan=5, sticky="w", pady=(8, 0))
        
        self.btn_add = ttk.Button(frm_buttons, text="Add line", command=self.on_add_row)
        self.btn_add.grid(row=0, column=0, padx=(0, 12))
        
        ttk.Button(frm_buttons, text="save CSV", command=self.export_csv).grid(row=0, column=1, padx=(0, 12))
        ttk.Button(frm_buttons, text="save PDF", command=self.export_pdf).grid(row=0, column=2, padx=(0, 12))
        ttk.Button(frm_buttons, text="Overall awards (PDF)", command=self.export_individual_reports).grid(row=0, column=3, padx=(0, 12))

        for c in range(5):
            frm_input.grid_columnconfigure(c, weight=0)
        frm_input.grid_columnconfigure(4, weight=1)

        # Tabelle (wird dynamisch aufgebaut)
        self.frm_table = ttk.Frame(self, padding=(10, 6))
        self.frm_table.pack(fill="both", expand=True)

    # =========================
    # Logo wählen
    # =========================
    def on_choose_logo(self):
        path = filedialog.askopenfilename(
            title="Logo-Datei auswählen",
            filetypes=[("Bilddateien", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("Alle Dateien", "*.*")],
        )
        if not path:
            return
        self.logo_path = path
        self.lbl_logo_name.config(text=os.path.basename(path))

    # =========================
    # Disziplinen toggeln
    # =========================
    def _on_toggle_disciplines(self):
        # UI und Tabelle neu aufbauen, Ränge/Total neu berechnen
        self._rebuild_dynamic_ui_and_tree()

    # =========================
    # Dynamische UI & Tree aufbauen
    # =========================
    def _rebuild_dynamic_ui_and_tree(self):
        # 1) Dynamische Eingabefelder neu erstellen
        for w in self.frm_dyn_inputs.winfo_children():
            w.destroy()
        self.disc_entries.clear()

        col = 0
        for d in DISCIPLINES:
            if self.disc_state[d.code].get():
                ttk.Label(self.frm_dyn_inputs, text=f"{d.label} (Erg):").grid(row=0, column=col, sticky="w", padx=(0, 4))
                ent = ttk.Entry(self.frm_dyn_inputs, width=8)
                ent.grid(row=0, column=col+1, sticky="w", padx=(0, 12))
                self.disc_entries[d.code] = ent
                col += 2

        # 2) Tabelle neu aufbauen (Spalten abhängig von aktiven Disziplinen)
        #    Wir zerstören/re-erstellen Treeview, übernehmen Reihenfolge & Daten.
        old_children = []
        if self.tree is not None:
            old_children = list(self.tree.get_children(""))
            # Reihenfolge merken
        for w in self.frm_table.winfo_children():
            w.destroy()
        self._build_tree()

        # 3) vorhandene Daten wieder einfügen
        #    Reihenfolge bleibt so, wie self.data gespeichert ist (durch Insert)
        for iid in self.data.keys():
            # Item in Tree anlegen, dann Werte aktualisieren
            new_iid = self.tree.insert("", "end", iid=iid, values=[""] * len(self.all_columns))
            self._update_tree_row(iid)

        # 4) Ränge/Total neu berechnen, da Disziplinen sich geändert haben
        self._recalc_ranks_and_update()

    # =========================
    # Tree dynamisch erzeugen
    # =========================
    def _build_tree(self):
        # Spalten zusammenstellen
        self.all_columns = []
        self.column_headers = {}
        self.column_widths = {}
        self.column_anchors = {}
        self.numeric_columns = set()

        # Basis-Spalten
        base_defs = [
            ("name", "Name", 200, "w", False),
            ("startnummer", "Startnr.", 80, "center", True),
            ("gesamt", "Gesamtpunkte", 120, "center", True),
            ("gesamtrang", "Gesamtrang", 100, "center", True),
        ]
        for key, hdr, w, anc, isnum in base_defs:
            self.all_columns.append(key)
            self.column_headers[key] = hdr
            self.column_widths[key] = w
            self.column_anchors[key] = anc
            if isnum:
                self.numeric_columns.add(key)

        # Disziplin-Spalten (nur aktive)
        for d in DISCIPLINES:
            if not self.disc_state[d.code].get():
                continue
            # Ergebnis
            key_e = f"{d.code}_erg"
            self.all_columns.append(key_e)
            self.column_headers[key_e] = f"{d.label} Erg"
            self.column_widths[key_e] = 90
            self.column_anchors[key_e] = "center"
            self.numeric_columns.add(key_e)
            # Punkte
            key_p = f"{d.code}_pkt"
            self.all_columns.append(key_p)
            self.column_headers[key_p] = f"{d.label} Pkt"
            self.column_widths[key_p] = 90
            self.column_anchors[key_p] = "center"
            self.numeric_columns.add(key_p)
            # Rang
            key_r = f"{d.code}_rang"
            self.all_columns.append(key_r)
            self.column_headers[key_r] = f"{d.label} Rang"
            self.column_widths[key_r] = 80
            self.column_anchors[key_r] = "center"
            self.numeric_columns.add(key_r)

        # Sichtbarkeit initialisieren/erhalten
        new_visibility = {}
        for key in self.all_columns:
            # bereits bekannte Einstellung übernehmen, sonst default sichtbar
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
        self.tree.configure(yscroll=yscroll.set, xscroll=xscroll.set)

        # Layout using grid to be more robust
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        self.frm_table.grid_rowconfigure(0, weight=1)
        self.frm_table.grid_columnconfigure(0, weight=1)

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
    # Spalten-Dialog (ein/ausblenden)
    # =========================
    def _open_columns_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Spalten ein-/ausblenden")
        dlg.transient(self)
        dlg.grab_set()
        frm = ttk.Frame(dlg, padding=10)
        frm.pack(fill="both", expand=True)

        vars_map = {}
        row = 0
        ttk.Label(frm, text="Sichtbare Spalten (nur aktuell verfügbare):", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w")
        row += 1
        for col in self.all_columns:
            v = tk.BooleanVar(value=self.column_visibility.get(col, True))
            vars_map[col] = v
            cb = ttk.Checkbutton(frm, text=self.column_headers[col], variable=v)
            cb.grid(row=row, column=0, sticky="w")
            row += 1

        btns = ttk.Frame(frm)
        btns.grid(row=row, column=0, pady=(8, 0), sticky="e")
        ttk.Button(btns, text="Abbrechen", command=dlg.destroy).pack(side="right", padx=(6, 0))
        def apply_and_close():
            # Sichtbarkeit anwenden
            for col, v in vars_map.items():
                self.column_visibility[col] = bool(v.get())
            self.display_columns = [c for c in self.all_columns if self.column_visibility.get(c, True)]
            try:
                self.tree["displaycolumns"] = self.display_columns
            except Exception:
                pass
            dlg.destroy()
        ttk.Button(btns, text="Übernehmen", command=apply_and_close).pack(side="right")

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
        used = {int(r.get("startnummer")) for r in self.data.values() if r.get("startnummer") is not None}
        n = 1
        while n in used:
            n += 1
        return n

    # =========================
    # Zeile hinzufügen
    # =========================
    def on_add_row(self):
        name = self.ent_name.get().strip()
        if not name:
            messagebox.showwarning("Eingabe fehlt", "Bitte einen Namen eingeben.")
            return

        try:
            startnr = self._parse_int(self.ent_startnr.get())
        except ValueError:
            messagebox.showwarning("Ungültige Startnummer", "Startnummer muss eine ganze Zahl sein.")
            return
        if startnr is None or any(row.get("startnummer") == startnr for row in self.data.values()):
            startnr = self._next_free_startnr()

        # Werte je aktive Disziplin erfassen
        disc_values = {}
        for d in DISCIPLINES:
            ent = self.disc_entries.get(d.code)
            if ent is None:
                disc_values[d.code] = None
            else:
                try:
                    v = self._parse_float(ent.get())
                except ValueError:
                    messagebox.showwarning("Ungültige Eingabe", f"{d.label}: Ergebnis muss Zahl sein.")
                    return
                disc_values[d.code] = v

        # Neue Zeile anlegen
        iid = self.tree.insert("", "end", values=[""] * len(self.all_columns))
        row = {"name": name, "startnummer": startnr, "gesamt": None, "gesamtrang": None}
        # Disziplin-Felder initialisieren
        for d in DISCIPLINES:
            row[f"{d.code}_erg"] = float(disc_values[d.code]) if disc_values[d.code] is not None else 0.0
            row[f"{d.code}_pkt"] = None
            row[f"{d.code}_rang"] = None

        self.data[iid] = row

        self._recalc_row(iid)
        self._update_tree_row(iid)
        self._recalc_ranks_and_update()

        # Eingaben leeren (Name darf stehen bleiben)
        self.ent_startnr.delete(0, "end")
        for ent in self.disc_entries.values():
            ent.delete(0, "end")

    # =========================
    # Zeile rechnen/anzeigen
    # =========================
    def _recalc_row(self, iid):
        row = self.data.get(iid)
        if not row:
            return
        # Punkte je Disziplin
        total = 0.0
        for d in DISCIPLINES:
            erg = row.get(f"{d.code}_erg") or 0.0
            pkt = d.points_func(erg)
            row[f"{d.code}_pkt"] = float(pkt)
            # Summe nur über aktive Disziplinen
            if self.disc_state[d.code].get():
                total += float(pkt)
        row["gesamt"] = total

    def _update_tree_row(self, iid):
        row = self.data[iid]
        values = []
        for col in self.all_columns:
            if col in ("name",):
                values.append(row["name"])
            elif col in ("startnummer", "gesamt", "gesamtrang"):
                values.append(self._format_number(row.get(col)))
            elif col.endswith("_erg") or col.endswith("_pkt") or col.endswith("_rang"):
                values.append(self._format_number(row.get(col)))
            else:
                values.append("")
        self.tree.item(iid, values=values)

    def _recalc_ranks_and_update(self):
        # Disziplin-Ränge (nur aktive Disziplinen) nach Punkten
        for d in DISCIPLINES:
            if not self.disc_state[d.code].get():
                # Inaktive Disziplin: Rang leeren
                for iid in self.data:
                    self.data[iid][f"{d.code}_rang"] = None
                continue
            if d.code == "fc":
                items = [(iid, self.data[iid].get(f"{d.code}_pkt")) for iid in self.data]
            else:
                items = [(iid, self.data[iid].get(f"{d.code}_erg")) for iid in self.data]
            ranks = compute_competition_ranks(items)
            for iid in self.data:
                self.data[iid][f"{d.code}_rang"] = ranks.get(iid)

        # Gesamtrang nach Gesamtpunkten
        items_total = [(iid, self.data[iid].get("gesamt")) for iid in self.data]
        ranks_total = compute_competition_ranks(items_total)
        for iid in self.data:
            self.data[iid]["gesamtrang"] = ranks_total.get(iid)
            self._update_tree_row(iid)

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
        col_key = self.tree["displaycolumns"][col_index]  # sichtbare Spalte
        # Editierbar: name, startnummer, *_erg (der aktiven!)
        editable = {"name", "startnummer"}
        for d in DISCIPLINES:
            if self.disc_state[d.code].get():
                editable.add(f"{d.code}_erg")

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

        # Validieren & übernehmen
        if col_key == "name":
            if new_text.strip() == "":
                messagebox.showwarning("Ungültiger Name", "Der Name darf nicht leer sein.")
                return
            self.data[iid]["name"] = new_text.strip()
            self._update_tree_row(iid)
            return

        if col_key == "startnummer":
            try:
                new_sn = int(new_text)
            except ValueError:
                messagebox.showwarning("Ungültige Startnummer", "Die Startnummer muss eine ganze Zahl sein.")
                return
            for oid in self.data:
                if oid != iid and self.data[oid].get("startnummer") == new_sn:
                    messagebox.showwarning("Doppelte Startnummer", f"Startnummer {new_sn} ist bereits vergeben.")
                    return
            self.data[iid]["startnummer"] = new_sn
            self._update_tree_row(iid)
            return

        # Disziplin-Ergebnis?
        if col_key.endswith("_erg"):
            try:
                new_val = self._parse_float(new_text, allow_empty=False)
            except ValueError:
                messagebox.showwarning("Ungültige Eingabe", "Bitte eine Zahl eingeben.")
                return
            self.data[iid][col_key] = float(new_val)
            # Zeile neu berechnen + Ränge aktualisieren
            self._recalc_row(iid)
            self._update_tree_row(iid)
            self._recalc_ranks_and_update()
            return

    def _cancel_inline_edit(self, event=None):
        if self._edit_entry:
            self._edit_entry.destroy()
        self._edit_entry = None
        self._edit_iid_col = None

    # =========================
    # Sortierung
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
            title="CSV speichern",
            defaultextension=".csv",
            filetypes=[("CSV-Datei", "*.csv")]
        )
        if not filename:
            return

        # Sichtbare Spalten in aktueller Reihenfolge exportieren
        cols = list(self.tree["displaycolumns"])
        headers = [self.column_headers[c] for c in cols]

        with open(filename, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(headers)
            for iid in self.tree.get_children():
                row = self.data[iid]
                out = []
                for c in cols:
                    out.append(row[c] if c in ("name",) else self._format_number(row.get(c)))
                w.writerow(out)

        messagebox.showinfo("Export erfolgreich", f"Die CSV wurde gespeichert:\n{filename}")

    # =========================
    # Export PDF Gesamtliste
    # =========================
    def export_pdf(self):
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        filename = filedialog.asksaveasfilename(
            title="PDF speichern",
            defaultextension=".pdf",
            filetypes=[("PDF-Datei", "*.pdf")]
        )
        if not filename:
            return

        from reportlab.lib.pagesizes import landscape
        doc = SimpleDocTemplate(
            filename,
            pagesize=landscape(A4),
            leftMargin=15*mm,
            rightMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm,
        )

        styles = getSampleStyleSheet()
        story = []

        title_text = self.ent_title.get().strip() or "Wettbewerb"
        story.append(Paragraph(title_text, styles["Title"]))
        story.append(Spacer(1, 6))

        # Tabelle: Basis + aktive Disziplinspalten (Erg/Pkt/Rang)
        headers = ["Name", "Startnr.", "Gesamt", "Gesamtrang"]
        col_keys = ["name", "startnummer", "gesamt", "gesamtrang"]
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
        base_widths = [45*mm, 11*mm, 11*mm, 11*mm]
        col_widths.extend(base_widths)
        for d in DISCIPLINES:
            if self.disc_state[d.code].get():
                col_widths.extend([11*mm, 11*mm, 9*mm])

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
            messagebox.showerror("PDF-Fehler", f"Beim Erstellen des PDFs ist ein Fehler aufgetreten:\n{e}")
            return

        messagebox.showinfo("Export erfolgreich", f"Die PDF wurde gespeichert:\n{filename}")

    # =========================
    # Export: Individuelle Berichte (A4, kompakte Disziplin-Tabelle, Logo)
    # =========================
    def export_individual_reports(self):
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        if not self.data:
            messagebox.showwarning("Keine Daten", "Es sind keine Teilnehmer vorhanden.")
            return

        # Update Ränge auf aktuelle Disziplinwahl
        self._recalc_ranks_and_update()

        create_separate = messagebox.askyesno(
            "PDF-Option",
            "Möchtest du einzelne PDF-Dateien pro Teilnehmer erstellen?\n"
            "Ja = einzelne PDFs\nNein = ein gemeinsames PDF"
        )

        # Sortierung: nach Gesamtrang, dann Name
        entries = sorted(
            self.data.items(),
            key=lambda kv: ((kv[1].get("gesamtrang") or 10**9), str(kv[1].get("name") or ""))
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=24, spaceAfter=6)
        h2_style = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=14, spaceBefore=6, spaceAfter=6)
        label_style = ParagraphStyle("Label", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=11)
        text_style = ParagraphStyle("Text", parent=styles["Normal"], fontSize=11)

        def make_logo():
            if not self.logo_path:
                return None
            try:
                img = Image(self.logo_path)
                max_w, max_h = 35*mm, 35*mm
                iw, ih = img.drawWidth, img.drawHeight
                scale = min(max_w/iw, max_h/ih)
                img.drawWidth = iw * scale
                img.drawHeight = ih * scale
                return img
            except Exception:
                return None

        title_text = self.ent_title.get().strip() or "Wettbewerb"

        def build_story_for_row(row):
            story = []
            logo = make_logo()
            if logo:
                head_tbl = Table([[Paragraph(title_text, title_style), logo]], colWidths=[None, 40*mm])
                head_tbl.setStyle(TableStyle([
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ]))
                story.append(head_tbl)
            else:
                story.append(Paragraph(title_text, title_style))
            story.append(Spacer(1, 6))

            # Teilnehmerkopf
            story.append(Paragraph("Teilnehmer", h2_style))
            info_tbl = Table([
                [Paragraph("Name:", label_style), Paragraph(str(row.get("name") or ""), text_style)],
                [Paragraph("Startnummer:", label_style), Paragraph(self._format_number(row.get("startnummer")), text_style)],
                [Paragraph("Gesamtpunkte:", label_style), Paragraph(self._format_number(row.get("gesamt")), text_style)],
                [Paragraph("Gesamtrang:", label_style), Paragraph(self._format_number(row.get("gesamtrang")), text_style)],
            ], colWidths=[40*mm, None])
            info_tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(info_tbl)
            story.append(Spacer(1, 10))

            # Kompakte Disziplin-Tabelle (nur aktive)
            tbl_headers = ["Disziplin", "Ergebnis", "Punkte", "Rang"]
            tbl_rows = []
            for d in DISCIPLINES:
                if not self.disc_state[d.code].get():
                    continue
                tbl_rows.append([
                    d.label,
                    self._format_number(row.get(f"{d.code}_erg")),
                    self._format_number(row.get(f"{d.code}_pkt")),
                    self._format_number(row.get(f"{d.code}_rang")),
                ])
            table_data = [tbl_headers] + tbl_rows
            disc_tbl = Table(table_data, colWidths=[28*mm, 28*mm, 28*mm, 22*mm])
            disc_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),

                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 10),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ]))
            story.append(disc_tbl)
            return story

        # Einzel-PDF je Teilnehmer?
        if create_separate:
            out_dir = filedialog.askdirectory(title="Zielordner für einzelne PDFs wählen")
            if not out_dir:
                return
            for iid, row in entries:
                sn = row.get("startnummer")
                name_safe = str(row.get("name") or "Teilnehmer").replace("/", "-")
                basename = f"{sn if sn is not None else ''}_{name_safe}".strip("_") + ".pdf"
                out_path = os.path.join(out_dir, basename)

                doc = SimpleDocTemplate(out_path, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm)
                story = build_story_for_row(row)
                try:
                    doc.build(story)
                except Exception as e:
                    messagebox.showerror("PDF-Fehler", f"Fehler bei '{out_path}':\n{e}")
                    return
            messagebox.showinfo("Fertig", f"Es wurden {len(entries)} individuelle PDFs erstellt.\nOrdner: {out_dir}")
            return

        # Sammel-PDF
        out_file = filedialog.asksaveasfilename(
            title="Gemeinsames PDF speichern",
            defaultextension=".pdf",
            filetypes=[("PDF-Datei", "*.pdf")]
        )
        if not out_file:
            return

        doc = SimpleDocTemplate(out_file, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm)
        story = []
        for idx, (iid, row) in enumerate(entries):
            story.extend(build_story_for_row(row))
            if idx < len(entries) - 1:
                story.append(PageBreak())
        try:
            doc.build(story)
        except Exception as e:
            messagebox.showerror("PDF-Fehler", f"Beim Erstellen des PDFs ist ein Fehler aufgetreten:\n{e}")
            return
        messagebox.showinfo("Export erfolgreich", f"Das PDF wurde gespeichert:\n{out_file}")

    # =========================
    # Start-/Hilfsfunktionen
    # =========================
    def _is_active(self, code):
        return bool(self.disc_state[code].get())


# ==============================
# Start
# ==============================
if __name__ == "__main__":
    app = ScoreTableApp()
    app.mainloop()

