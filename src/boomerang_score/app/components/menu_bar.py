"""Menu bar component with export actions."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog


class MenuBar:
    """
    Application menu bar with File and View menus.

    Provides access to export functions (CSV, PDF) and view options
    (column management).
    """

    def __init__(self, root, export_service, table_view, competition):
        """
        Initialize the menu bar.

        Args:
            root: Root Tk window
            export_service: ExportService instance
            table_view: ParticipantTableView instance
            competition: Competition instance
        """
        self.root = root
        self.export_service = export_service
        self.table_view = table_view
        self.competition = competition

        self.menubar = tk.Menu(root)
        root.config(menu=self.menubar)

    def build(self):
        """Build the menu bar."""
        # View menu
        view_menu = tk.Menu(self.menubar, tearoff=False)
        self.menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Manage columns …",
                            command=lambda: self.table_view.open_columns_dialog(self.root))

    def export_csv(self):
        """Export visible columns to CSV."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not filename:
            return

        try:
            visible_cols = self.table_view.display_columns
            self.export_service.export_csv(filename, visible_cols)
            messagebox.showinfo("Export CSV", f"Data exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export CSV:\n{e}")

    def export_pdf(self):
        """Export full list to PDF."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if not filename:
            return

        try:
            logo_path = getattr(self.competition, 'logo_path', None)
            self.export_service.export_pdf_full_list(filename, logo_path)
            messagebox.showinfo("Export PDF", f"PDF created:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to create PDF:\n{e}")

    def export_individual_reports(self):
        """Export individual participant reports."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("DOCX files", "*.docx"), ("All files", "*.*")]
        )
        if not filename:
            return

        try:
            logo_path = getattr(self.competition, 'logo_path', None)
            self.export_service.export_individual_reports(filename, logo_path)
            messagebox.showinfo("Export", f"Individual reports created:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to create reports:\n{e}")
