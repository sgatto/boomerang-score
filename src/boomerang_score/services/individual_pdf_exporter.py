from typing import Optional

from boomerang_score.services.participant_report_page import ParticipantReportPage


class IndividualPdfExporter:
    """Handles exporting individual participant award reports to PDF."""

    def __init__(self, competition, disciplines: dict):
        """
        Args:
            competition: Competition instance
            disciplines: Dict mapping discipline code to discipline object
        """
        self.competition = competition
        self.disciplines = disciplines

    def build_pdf_styles(self):
        """Build and return the paragraph styles used in individual PDF reports."""
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CenteredTitle",
            parent=styles["Title"],
            fontSize=20,
            spaceAfter=6,
            alignment=1,
        )
        h2_style = ParagraphStyle(
            "CenteredH2",
            parent=styles["Heading2"],
            fontSize=14,
            spaceAfter=6,
            alignment=1,
        )
        label_style = ParagraphStyle(
            "Label", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=11
        )
        text_style = ParagraphStyle("Text", parent=styles["Normal"], fontSize=11)
        return styles, title_style, h2_style, label_style, text_style

    def build_participant_page(
        self, participant, title_text, logo_path, title_style, h2_style, label_style, text_style
    ):
        """Build the list of story elements for a single participant page."""
        page = ParticipantReportPage(self.competition, self.disciplines)
        return page.build(
            participant, title_text, logo_path,
            title_style, h2_style, label_style, text_style,
        )

    def export(self, filename: str, participant_order: list[str], logo_path: Optional[str]):
        """Export individual reports to PDF."""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, PageBreak

        _styles, title_style, h2_style, label_style, text_style = self.build_pdf_styles()

        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
        )

        story = []
        title_text = self.competition.title or "Competition"

        for idx, participant_id in enumerate(participant_order):
            try:
                pid = int(participant_id)
            except (ValueError, TypeError):
                continue
            participant = self.competition.get_participant(pid)
            if not participant:
                continue

            story.extend(
                self.build_participant_page(
                    participant, title_text, logo_path,
                    title_style, h2_style, label_style, text_style,
                )
            )

            if idx < len(participant_order) - 1:
                story.append(PageBreak())

        doc.build(story)
