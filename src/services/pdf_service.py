"""
PDF service for the Quiz App.

This module provides PDF report generation functionality
for surveys, responses, and analytics.
"""

from datetime import datetime
import io
import json
import logging
from pathlib import Path
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.platypus.flowables import PageBreak

logger = logging.getLogger(__name__)


class PDFService:
    """Service for generating PDF reports."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()

    def setup_custom_styles(self):
        """Setup custom styles for PDF generation."""
        # Custom styles matching the app's theme
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Title"],
                fontSize=24,
                textColor=HexColor("#8B5CF6"),  # Primary Purple
                alignment=TA_CENTER,
                spaceAfter=30,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="CustomHeading",
                parent=self.styles["Heading1"],
                fontSize=16,
                textColor=HexColor("#F59E0B"),  # Accent Gold
                spaceAfter=12,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="CustomSubheading",
                parent=self.styles["Heading2"],
                fontSize=14,
                textColor=HexColor("#374151"),  # Dark gray
                spaceAfter=8,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="CustomBody",
                parent=self.styles["Normal"],
                fontSize=11,
                textColor=HexColor("#1F2937"),  # Dark Background
                spaceAfter=6,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="CustomCaption",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=HexColor("#6B7280"),  # Gray
                alignment=TA_CENTER,
                spaceAfter=4,
            )
        )

    def generate_survey_report(
        self,
        survey_data: dict[str, Any],
        responses_data: list[dict[str, Any]],
        analytics_data: dict[str, Any],
    ) -> bytes:
        """
        Generate PDF report for a survey.

        Args:
            survey_data: Survey information
            responses_data: List of responses
            analytics_data: Analytics data

        Returns:
            PDF bytes
        """
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1 * inch)
            story = []

            # Title
            title = Paragraph(
                f"Survey Report: {survey_data['title']}", self.styles["CustomTitle"]
            )
            story.append(title)
            story.append(Spacer(1, 20))

            # Survey information
            story.append(Paragraph("Survey Information", self.styles["CustomHeading"]))

            survey_info = [
                ["Survey ID:", str(survey_data["id"])],
                ["Title:", survey_data["title"]],
                ["Description:", survey_data.get("description", "No description")],
                ["Status:", "Active" if survey_data["is_active"] else "Inactive"],
                ["Type:", "Public" if survey_data["is_public"] else "Private"],
                ["Created:", survey_data["created_at"]],
                ["Total Questions:", str(analytics_data.get("total_questions", 0))],
                ["Total Responses:", str(analytics_data.get("total_responses", 0))],
            ]

            survey_table = Table(survey_info, colWidths=[2 * inch, 4 * inch])
            survey_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), HexColor("#F3F4F6")),
                        ("TEXTCOLOR", (0, 0), (-1, -1), HexColor("#1F2937")),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("GRID", (0, 0), (-1, -1), 1, HexColor("#E5E7EB")),
                    ]
                )
            )

            story.append(survey_table)
            story.append(Spacer(1, 20))

            # Analytics summary
            story.append(Paragraph("Analytics Summary", self.styles["CustomHeading"]))

            analytics_info = [
                [
                    "Unique Respondents:",
                    str(analytics_data.get("unique_respondents", 0)),
                ],
                [
                    "Completion Rate:",
                    f"{analytics_data.get('completion_rate', 0):.1f}%",
                ],
                [
                    "Authenticated Users:",
                    str(analytics_data.get("authenticated_users", 0)),
                ],
                ["First Response:", analytics_data.get("first_response", "N/A")],
                ["Last Response:", analytics_data.get("last_response", "N/A")],
            ]

            analytics_table = Table(analytics_info, colWidths=[2 * inch, 4 * inch])
            analytics_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), HexColor("#F3F4F6")),
                        ("TEXTCOLOR", (0, 0), (-1, -1), HexColor("#1F2937")),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("GRID", (0, 0), (-1, -1), 1, HexColor("#E5E7EB")),
                    ]
                )
            )

            story.append(analytics_table)
            story.append(Spacer(1, 20))

            # Responses summary
            if responses_data:
                story.append(
                    Paragraph("Responses Summary", self.styles["CustomHeading"])
                )

                # Group responses by question
                questions_responses = {}
                for response in responses_data:
                    question_id = response["question"]["id"]
                    if question_id not in questions_responses:
                        questions_responses[question_id] = {
                            "question": response["question"],
                            "responses": [],
                        }
                    questions_responses[question_id]["responses"].append(response)

                # Generate summary for each question
                for question_id, data in questions_responses.items():
                    question = data["question"]
                    responses = data["responses"]

                    story.append(
                        Paragraph(
                            f"Question: {question['title']}",
                            self.styles["CustomSubheading"],
                        )
                    )
                    story.append(
                        Paragraph(
                            f"Type: {question['type']}", self.styles["CustomBody"]
                        )
                    )
                    story.append(
                        Paragraph(
                            f"Total Responses: {len(responses)}",
                            self.styles["CustomBody"],
                        )
                    )

                    # Show response samples
                    if responses:
                        story.append(
                            Paragraph("Sample Responses:", self.styles["CustomBody"])
                        )

                        sample_responses = responses[:5]  # Show first 5 responses
                        for i, response in enumerate(sample_responses, 1):
                            answer_text = self._format_answer(response["answer"])
                            story.append(
                                Paragraph(
                                    f"{i}. {answer_text}", self.styles["CustomBody"]
                                )
                            )

                        if len(responses) > 5:
                            story.append(
                                Paragraph(
                                    f"... and {len(responses) - 5} more responses",
                                    self.styles["CustomCaption"],
                                )
                            )

                    story.append(Spacer(1, 15))

            # Page break for detailed responses
            if responses_data:
                story.append(PageBreak())
                story.append(
                    Paragraph("Detailed Responses", self.styles["CustomHeading"])
                )

                # Create detailed responses table
                response_headers = ["#", "Question", "Answer", "User", "Date"]
                response_rows = [response_headers]

                for i, response in enumerate(
                    responses_data[:100], 1
                ):  # Limit to 100 responses
                    user_info = "Anonymous"
                    if response.get("user"):
                        user_info = response["user"].get("display_name", "Unknown")

                    answer_text = self._format_answer(response["answer"])
                    date_str = response["created_at"][:10]  # Just the date part

                    response_rows.append(
                        [
                            str(i),
                            response["question"]["title"][:30] + "..."
                            if len(response["question"]["title"]) > 30
                            else response["question"]["title"],
                            answer_text[:50] + "..."
                            if len(answer_text) > 50
                            else answer_text,
                            user_info,
                            date_str,
                        ]
                    )

                if len(response_rows) > 1:
                    response_table = Table(
                        response_rows,
                        colWidths=[
                            0.5 * inch,
                            2 * inch,
                            2 * inch,
                            1.5 * inch,
                            1 * inch,
                        ],
                    )
                    response_table.setStyle(
                        TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#8B5CF6")),
                                ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
                                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                                ("FONTSIZE", (0, 0), (-1, -1), 9),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                                ("GRID", (0, 0), (-1, -1), 1, HexColor("#E5E7EB")),
                                (
                                    "ROWBACKGROUNDS",
                                    (0, 1),
                                    (-1, -1),
                                    [HexColor("#FFFFFF"), HexColor("#F9FAFB")],
                                ),
                            ]
                        )
                    )

                    story.append(response_table)

                    if len(responses_data) > 100:
                        story.append(Spacer(1, 10))
                        story.append(
                            Paragraph(
                                f"Note: Showing first 100 of {len(responses_data)} total responses",
                                self.styles["CustomCaption"],
                            )
                        )

            # Footer
            story.append(Spacer(1, 30))
            story.append(
                Paragraph("Report generated by Quiz App", self.styles["CustomCaption"])
            )
            story.append(
                Paragraph(
                    f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    self.styles["CustomCaption"],
                )
            )

            # Build PDF
            doc.build(story)

            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()

            return pdf_bytes

        except Exception as e:
            logger.error(f"Error generating survey report: {e!s}")
            raise

    def _format_answer(self, answer: dict[str, Any]) -> str:
        """Format answer data for display."""
        if isinstance(answer, dict):
            if "value" in answer:
                return str(answer["value"])
            elif "text" in answer:
                return str(answer["text"])
            else:
                return json.dumps(answer)
        else:
            return str(answer)

    def generate_user_report(
        self, user_data: dict[str, Any], user_responses: list[dict[str, Any]]
    ) -> bytes:
        """
        Generate PDF report for a user's responses.

        Args:
            user_data: User information
            user_responses: List of user's responses

        Returns:
            PDF bytes
        """
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1 * inch)
            story = []

            # Title
            title = Paragraph(
                f"User Report: {user_data.get('display_name', 'Unknown User')}",
                self.styles["CustomTitle"],
            )
            story.append(title)
            story.append(Spacer(1, 20))

            # User information
            story.append(Paragraph("User Information", self.styles["CustomHeading"]))

            user_info = [
                ["User ID:", str(user_data["id"])],
                ["Display Name:", user_data.get("display_name", "Unknown")],
                ["Username:", user_data.get("username", "N/A")],
                ["Email:", user_data.get("email", "N/A")],
                ["Telegram ID:", str(user_data.get("telegram_id", "N/A"))],
                ["Created:", user_data.get("created_at", "N/A")],
                ["Total Responses:", str(len(user_responses))],
            ]

            user_table = Table(user_info, colWidths=[2 * inch, 4 * inch])
            user_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), HexColor("#F3F4F6")),
                        ("TEXTCOLOR", (0, 0), (-1, -1), HexColor("#1F2937")),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("GRID", (0, 0), (-1, -1), 1, HexColor("#E5E7EB")),
                    ]
                )
            )

            story.append(user_table)
            story.append(Spacer(1, 20))

            # User responses
            if user_responses:
                story.append(Paragraph("User Responses", self.styles["CustomHeading"]))

                for i, response in enumerate(user_responses, 1):
                    story.append(
                        Paragraph(
                            f"{i}. {response['question']['title']}",
                            self.styles["CustomSubheading"],
                        )
                    )
                    story.append(
                        Paragraph(
                            f"Question Type: {response['question']['type']}",
                            self.styles["CustomBody"],
                        )
                    )

                    answer_text = self._format_answer(response["answer"])
                    story.append(
                        Paragraph(f"Answer: {answer_text}", self.styles["CustomBody"])
                    )

                    story.append(
                        Paragraph(
                            f"Responded on: {response['created_at']}",
                            self.styles["CustomCaption"],
                        )
                    )
                    story.append(Spacer(1, 15))

            # Footer
            story.append(Spacer(1, 30))
            story.append(
                Paragraph("Report generated by Quiz App", self.styles["CustomCaption"])
            )
            story.append(
                Paragraph(
                    f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    self.styles["CustomCaption"],
                )
            )

            # Build PDF
            doc.build(story)

            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()

            return pdf_bytes

        except Exception as e:
            logger.error(f"Error generating user report: {e!s}")
            raise

    def save_pdf_to_file(self, pdf_bytes: bytes, filename: str) -> str:
        """
        Save PDF bytes to file.

        Args:
            pdf_bytes: PDF content bytes
            filename: Output filename

        Returns:
            Path to saved file
        """
        try:
            # Create reports directory if it doesn't exist
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)

            # Save PDF file
            file_path = reports_dir / filename
            with open(file_path, "wb") as f:
                f.write(pdf_bytes)

            return str(file_path)

        except Exception as e:
            logger.error(f"Error saving PDF to file: {e!s}")
            raise


# Global PDF service instance
pdf_service = PDFService()


def generate_survey_pdf_report(
    survey_data: dict[str, Any],
    responses_data: list[dict[str, Any]],
    analytics_data: dict[str, Any],
) -> bytes:
    """
    Convenience function to generate survey PDF report.

    Args:
        survey_data: Survey information
        responses_data: List of responses
        analytics_data: Analytics data

    Returns:
        PDF bytes
    """
    return pdf_service.generate_survey_report(
        survey_data, responses_data, analytics_data
    )


def generate_user_pdf_report(
    user_data: dict[str, Any], user_responses: list[dict[str, Any]]
) -> bytes:
    """
    Convenience function to generate user PDF report.

    Args:
        user_data: User information
        user_responses: List of user's responses

    Returns:
        PDF bytes
    """
    return pdf_service.generate_user_report(user_data, user_responses)
