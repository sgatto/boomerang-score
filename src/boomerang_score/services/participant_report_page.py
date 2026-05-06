from typing import Optional

from boomerang_score.services.export_service import format_number


class ParticipantReportPage:
    """Builds the PDF story elements for a single participant award page."""

    def __init__(self, competition, disciplines: dict):
        """
        Args:
            competition: Competition instance
            disciplines: Dict mapping discipline code to discipline object
        """
        self.competition = competition
        self.disciplines = disciplines

    def make_logo(self, logo_path: Optional[str]):
        """Load and scale a logo image for use in the report."""
        from reportlab.lib.units import mm
        from reportlab.platypus import Image

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

    def build_info_table(self, participant, label_style, text_style):
        """Build the participant info table (name, total points, overall rank)."""
        from reportlab.lib.units import mm
        from reportlab.platypus import Table, TableStyle, Paragraph

        info_tbl = Table(
            [
                [
                    Paragraph("Name:", label_style),
                    Paragraph(participant.name, text_style),
                ],
                [
                    Paragraph("Total Points:", label_style),
                    Paragraph(format_number(participant.total_points), text_style),
                ],
                [
                    Paragraph("Overall Rank:", label_style),
                    Paragraph(format_number(participant.overall_rank), text_style),
                ],
            ],
            colWidths=[40 * mm, None],
        )
        info_tbl.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 2),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        info_tbl.hAlign = "CENTER"
        return info_tbl

    def build_discipline_table(self, participant):
        """Build the discipline results table for the participant."""
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import Table, TableStyle

        tbl_headers = ["Discipline", "Result", "Points", "Rank"]
        tbl_rows = [
            [
                self.disciplines[disc_code].label,
                format_number(participant.get_result(disc_code)),
                format_number(participant.get_points(disc_code)),
                format_number(participant.get_rank(disc_code)),
            ]
            for disc_code in sorted(self.competition.active_disciplines)
            if disc_code in self.disciplines
        ]

        disc_tbl = Table(
            [tbl_headers] + tbl_rows,
            colWidths=[28 * mm, 28 * mm, 28 * mm, 22 * mm],
        )
        disc_tbl.setStyle(
            TableStyle(
                [
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
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.whitesmoke, colors.white],
                    ),
                ]
            )
        )
        return disc_tbl

    def build(self, participant, title_text, logo_path, title_style, h2_style, label_style, text_style):
        """Return the list of story elements for this participant's page."""
        from reportlab.platypus import Paragraph, Spacer

        elements = []
        elements.append(Paragraph(title_text, title_style))
        elements.append(Spacer(1, 6))
        elements.append(
            Paragraph('<para alignment="center">Overall award</para>', h2_style)
        )
        elements.append(Spacer(1, 6))

        logo = self.make_logo(logo_path)
        if logo:
            logo.hAlign = "CENTER"
            elements.append(logo)
        elements.append(Spacer(1, 20))

        elements.append(self.build_info_table(participant, label_style, text_style))
        elements.append(Spacer(1, 30))
        elements.append(self.build_discipline_table(participant))
        return elements
