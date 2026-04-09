"""Export functionality for competitions."""

import csv
from typing import Optional


def format_number(value) -> str:
    """Format a numeric value for display."""
    if value is None:
        return ""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(f - int(f)) < 1e-9:
        return str(int(f))
    return f"{f:.2f}"


class ExportService:
    """Service for exporting competition data."""

    def __init__(self, competition, disciplines):
        """
        Initialize export service.

        Args:
            competition: Competition instance
            disciplines: List of discipline definitions
        """
        self.competition = competition
        self.disciplines = {d.code: d for d in disciplines}

    def export_csv(self, filename: str, visible_columns: list[str],
                   column_headers: dict[str, str], participant_order: list[str]):
        """
        Export competition data to CSV.

        Args:
            filename: Output file path
            visible_columns: List of column keys to export
            column_headers: Dict mapping column keys to display names
            participant_order: List of participant IDs in display order
        """
        headers = [column_headers[c] for c in visible_columns]

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(headers)

            for participant_id in participant_order:
                participant = self.competition.get_participant(participant_id)
                if not participant:
                    continue

                row = []
                for col in visible_columns:
                    if col == "name":
                        row.append(participant.name)
                    elif col == "startnumber":
                        row.append(format_number(participant.startnumber))
                    elif col == "total":
                        row.append(format_number(participant.total_points))
                    elif col == "overall_rank":
                        row.append(format_number(participant.overall_rank))
                    elif col.endswith("_res"):
                        disc_code = col[:-4]
                        row.append(format_number(participant.get_result(disc_code)))
                    elif col.endswith("_pts"):
                        disc_code = col[:-4]
                        row.append(format_number(participant.get_points(disc_code)))
                    elif col.endswith("_rank"):
                        disc_code = col[:-5]
                        row.append(format_number(participant.get_rank(disc_code)))
                    else:
                        row.append("")

                writer.writerow(row)

    def export_pdf_full_list(self, filename: str, participant_order: list[str]):
        """
        Export full competition list to PDF.

        Args:
            filename: Output file path
            participant_order: List of participant IDs in display order
        """
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

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

        # Title
        title_text = self.competition.title or "Competition"
        story.append(Paragraph(title_text, styles["Title"]))
        story.append(Spacer(1, 6))

        # Build table headers and column keys
        headers = ["Name", "Start No.", "Total", "Overall Rank"]
        col_keys = ["name", "startnumber", "total", "overall_rank"]

        # Add active discipline columns
        active_disciplines = [
            (code, self.disciplines[code])
            for code in sorted(self.competition.active_disciplines)
            if code in self.disciplines
        ]

        for disc_code, disc in active_disciplines:
            headers += [f"{disc.label} Res", f"{disc.label} Pts", f"{disc.label} Rank"]
            col_keys += [f"{disc_code}_res", f"{disc_code}_pts", f"{disc_code}_rank"]

        # Build data rows
        data_rows = []
        for participant_id in participant_order:
            participant = self.competition.get_participant(participant_id)
            if not participant:
                continue

            row_vals = []
            for key in col_keys:
                if key == "name":
                    row_vals.append(participant.name)
                elif key == "startnumber":
                    row_vals.append(format_number(participant.startnumber))
                elif key == "total":
                    row_vals.append(format_number(participant.total_points))
                elif key == "overall_rank":
                    row_vals.append(format_number(participant.overall_rank))
                elif key.endswith("_res"):
                    disc_code = key[:-4]
                    row_vals.append(format_number(participant.get_result(disc_code)))
                elif key.endswith("_pts"):
                    disc_code = key[:-4]
                    row_vals.append(format_number(participant.get_points(disc_code)))
                elif key.endswith("_rank"):
                    disc_code = key[:-5]
                    row_vals.append(format_number(participant.get_rank(disc_code)))

            data_rows.append(row_vals)

        table_data = [headers] + data_rows

        # Column widths
        col_widths = [45*mm, 11*mm, 11*mm, 11*mm]  # Base columns
        for _ in active_disciplines:
            col_widths.extend([11*mm, 11*mm, 9*mm])  # Discipline columns

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

        doc.build(story)

    def export_individual_reports(self, filename: str, participant_order: list[str],
                                  logo_path: Optional[str] = None):
        """
        Export individual awards to PDF or DOCX.

        Args:
            filename: Output file path
            participant_order: List of participant IDs in display order
            logo_path: Optional path to logo image
        """
        is_pdf = filename.lower().endswith(".pdf")
        is_docx = filename.lower().endswith(".docx")

        if is_docx:
            self._export_individual_docx(filename, participant_order, logo_path)
        elif is_pdf:
            self._export_individual_pdf(filename, participant_order, logo_path)
        else:
            raise ValueError("Filename must end with .pdf or .docx")

    def _export_individual_pdf(self, filename: str, participant_order: list[str],
                               logo_path: Optional[str]):
        """Export individual reports to PDF."""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                       Paragraph, Spacer, Image, PageBreak)
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ReportTitle", parent=styles["Title"],
            fontName="Helvetica-Bold", fontSize=20, leading=24, spaceAfter=6
        )
        h2_style = ParagraphStyle(
            "H2", parent=styles["Heading2"],
            fontName="Helvetica-Bold", fontSize=14,
            spaceBefore=6, spaceAfter=6, alignment=1
        )

        def make_logo():
            if not logo_path:
                return None
            try:
                img = Image(logo_path)
                max_w, max_h = 160 * mm, 160 * mm
                iw, ih = img.imageWidth, img.imageHeight
                scale = min(max_w / iw, max_h / ih)
                img.drawWidth = iw * scale
                img.drawHeight = ih * scale
                return img
            except Exception:
                return None

        doc = SimpleDocTemplate(
            filename, pagesize=A4,
            leftMargin=18*mm, rightMargin=18*mm,
            topMargin=16*mm, bottomMargin=16*mm
        )

        story = []
        title_text = self.competition.title or "Competition"

        for idx, participant_id in enumerate(participant_order):
            participant = self.competition.get_participant(participant_id)
            if not participant:
                continue

            # Title and header
            story.append(Paragraph(title_text, title_style))
            story.append(Spacer(1, 6))
            story.append(Paragraph('<para alignment="center">Overall award</para>', h2_style))
            story.append(Spacer(1, 6))

            # Logo
            logo = make_logo()
            if logo:
                logo.hAlign = "CENTER"
                story.append(logo)
            story.append(Spacer(1, 20))

            # Participant info table
            label_style = ParagraphStyle("Label", parent=styles["Normal"],
                                        fontName="Helvetica-Bold", fontSize=11)
            text_style = ParagraphStyle("Text", parent=styles["Normal"], fontSize=11)

            info_tbl = Table([
                [Paragraph("Name:", label_style),
                 Paragraph(participant.name, text_style)],
                [Paragraph("Total Points:", label_style),
                 Paragraph(format_number(participant.total_points), text_style)],
                [Paragraph("Overall Rank:", label_style),
                 Paragraph(format_number(participant.overall_rank), text_style)]
            ], colWidths=[40*mm, None])
            info_tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]))
            info_tbl.hAlign = "CENTER"
            story.append(info_tbl)
            story.append(Spacer(1, 30))

            # Discipline results table
            tbl_headers = ["Discipline", "Result", "Points", "Rank"]
            tbl_rows = []

            for disc_code in sorted(self.competition.active_disciplines):
                if disc_code not in self.disciplines:
                    continue
                disc = self.disciplines[disc_code]
                tbl_rows.append([
                    disc.label,
                    format_number(participant.get_result(disc_code)),
                    format_number(participant.get_points(disc_code)),
                    format_number(participant.get_rank(disc_code)),
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

            # Page break between participants
            if idx < len(participant_order) - 1:
                story.append(PageBreak())

        doc.build(story)

    def _export_individual_docx(self, filename: str, participant_order: list[str],
                                logo_path: Optional[str]):
        """Export individual reports to DOCX."""
        from docx import Document
        from docx.shared import Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_TABLE_ALIGNMENT

        doc = Document()
        title_text = self.competition.title or "Competition"

        for idx, participant_id in enumerate(participant_order):
            participant = self.competition.get_participant(participant_id)
            if not participant:
                continue

            # Title
            h = doc.add_heading(title_text, level=1)
            h.alignment = WD_ALIGN_PARAGRAPH.CENTER

            h2 = doc.add_heading("Overall award", level=2)
            h2.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Logo
            if logo_path:
                try:
                    doc.add_picture(logo_path, width=Inches(2.0))
                    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
                except Exception:
                    pass

            doc.add_paragraph("")

            # Participant info
            table = doc.add_table(rows=0, cols=2)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER

            def add_info(label, value):
                r = table.add_row().cells
                r[0].text = label
                r[1].text = str(value)

            add_info("Name:", participant.name)
            add_info("Total Points:", format_number(participant.total_points))
            add_info("Overall Rank:", format_number(participant.overall_rank))

            doc.add_paragraph("")

            # Discipline table
            disc_table = doc.add_table(rows=1, cols=4)
            disc_table.style = "Table Grid"
            hdr = disc_table.rows[0].cells
            hdr[0].text = "Discipline"
            hdr[1].text = "Result"
            hdr[2].text = "Points"
            hdr[3].text = "Rank"

            for disc_code in sorted(self.competition.active_disciplines):
                if disc_code not in self.disciplines:
                    continue
                disc = self.disciplines[disc_code]
                row_cells = disc_table.add_row().cells
                row_cells[0].text = disc.label
                row_cells[1].text = format_number(participant.get_result(disc_code))
                row_cells[2].text = format_number(participant.get_points(disc_code))
                row_cells[3].text = format_number(participant.get_rank(disc_code))

            # Page break between participants
            if idx < len(participant_order) - 1:
                doc.add_page_break()

        doc.save(filename)
