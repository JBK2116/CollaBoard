from pathlib import Path
from typing import Any

from django.conf import settings
from django.urls import reverse
from fpdf import FPDF

from apps.api import utils

FILE_TYPE: utils.FileTypes = utils.FileTypes.PDF


class MeetingSummaryPDF(FPDF):
    def __init__(self):
        with open("/tmp/debug.log", "a") as f:
            f.write("MeetingSummaryPDF.__init__ called\n")

        super().__init__()

        font_path = (
            Path(settings.STATICFILES_DIRS[0]) / "fonts" / "dejavu-sans.book.ttf"
        )

        with open("/tmp/debug.log", "a") as f:
            f.write(f"Font path: {font_path}\n")
            f.write(f"Font exists: {font_path.exists()}\n")

        if not font_path.exists():
            raise FileNotFoundError(f"Font file not found: {font_path}")

        self.add_font("DejaVuSans", "", str(font_path), uni=True)
        with open("/tmp/debug.log", "a") as f:
            f.write("Font added successfully\n")

        self.set_font("DejaVuSans", "", 12)  # default font
        self.set_auto_page_break(auto=True, margin=15)

        with open("/tmp/debug.log", "a") as f:
            f.write("MeetingSummaryPDF.__init__ completed\n")

    # --- HEADER / FOOTER ---
    def header(self):
        if self.page_no() > 1:
            self.set_font("DejaVuSans", "", 9)
            self.set_text_color(150, 150, 150)
            self.cell(0, 8, "Meeting Summary", 0, 1, "C")
            self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVuSans", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

    # --- TITLE PAGE ---
    def add_title_page(
        self, title_text, description, date_text, time_created_text, author_text
    ):
        self.set_font("DejaVuSans", "", 24)
        self.set_text_color(0, 0, 0)
        self.ln(40)
        self.cell(0, 15, title_text, 0, 1, "C")

        self.set_font("DejaVuSans", "", 14)
        self.set_text_color(90, 90, 90)
        self.multi_cell(0, 8, description, 0, "C")
        self.ln(20)

        self.set_font("DejaVuSans", "", 12)
        self.set_text_color(60, 60, 60)
        self.cell(0, 8, f"📅 Date Created: {date_text}", 0, 1, "C")
        self.cell(0, 8, f"🕒 Created At: {time_created_text}", 0, 1, "C")
        self.cell(0, 8, f"🎯 Director: {author_text}", 0, 1, "C")
        self.ln(20)

    # --- SECTION HEADINGS ---
    def section_heading(self, text):
        self.set_font("DejaVuSans", "", 16)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, text, 0, 1, "L")
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.5)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(6)

    # --- QUESTION SECTION ---
    def add_question_section(self, question_text, response_count_text, summary_text):
        if self.get_y() > 220:
            self.add_page()

        self.section_heading(question_text)
        self.set_font("DejaVuSans", "", 12)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, f"Total Responses: {response_count_text}", 0, 1, "L")
        self.ln(2)

        self.set_font("DejaVuSans", "", 11)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, summary_text, 0, "J")
        self.ln(8)

    # --- KEY TAKEAWAYS ---
    def add_key_takeaways_section(self, key_takeaways):
        self.add_page()
        self.section_heading("Key Takeaways")
        self.set_font("DejaVuSans", "", 11)
        self.set_text_color(0, 0, 0)

        for index, text in enumerate(key_takeaways, start=1):
            self.set_x(self.l_margin + 5)
            self.multi_cell(0, 6, f"{index}. {text}", 0, "L")
            self.ln(2)


def generate_pdf(data: dict[str, Any], meeting_id: str) -> tuple[bool, str | None]:
    """
    Creates a PDF meeting summary and saves it.
    """
    with open("/tmp/debug.log", "a") as f:
        f.write("=== PDF GENERATION START ===\n")

    try:
        export_path: Path = utils.get_export_path()
        filename: str = utils.generate_filename(
            meeting_id=meeting_id, file_type=FILE_TYPE
        )
        file_path: Path = utils.generate_file_path(
            export_path=export_path, filename=filename
        )

        with open("/tmp/debug.log", "a") as f:
            f.write(f"PDF paths generated - file_path: {file_path}\n")

        meeting_metadata: dict[str, Any] | None = utils.get_meeting_metadata(data=data)
        if not meeting_metadata:
            with open("/tmp/debug.log", "a") as f:
                f.write("PDF FAILED: meeting_metadata is None\n")
            return (False, None)

        questions_analysis_dictionaries: list[dict[str, Any]] | None = (
            utils.get_summarized_meeting_question_analysis(data=data)
        )
        if not questions_analysis_dictionaries:
            with open("/tmp/debug.log", "a") as f:
                f.write("PDF FAILED: questions_analysis_dictionaries is None\n")
            return (False, None)

        key_takeaways: list[str] | None = utils.get_summarized_meeting_key_takeaways(
            data=data
        )
        if not key_takeaways:
            with open("/tmp/debug.log", "a") as f:
                f.write("PDF FAILED: key_takeaways is None\n")
            return (False, None)

        with open("/tmp/debug.log", "a") as f:
            f.write("PDF: All validations passed, creating PDF object...\n")

        pdf = MeetingSummaryPDF()

        with open("/tmp/debug.log", "a") as f:
            f.write("PDF: MeetingSummaryPDF object created successfully\n")

        pdf.add_page()

        with open("/tmp/debug.log", "a") as f:
            f.write("PDF: Page added successfully\n")

        # Title page
        pdf.add_title_page(
            meeting_metadata.get("title", ""),
            meeting_metadata.get("description", ""),
            meeting_metadata.get("date", ""),
            meeting_metadata.get("time_created", ""),
            meeting_metadata.get("author", ""),
        )

        with open("/tmp/debug.log", "a") as f:
            f.write("PDF: Title page added successfully\n")

        # Questions & Summaries
        for i, question_summary in enumerate(questions_analysis_dictionaries):
            pdf.add_question_section(
                question_summary.get("question", ""),
                question_summary.get("response_count", ""),
                question_summary.get("summary", ""),
            )
            with open("/tmp/debug.log", "a") as f:
                f.write(f"PDF: Question section {i} added successfully\n")

        # Key Takeaways
        pdf.add_key_takeaways_section(key_takeaways)

        with open("/tmp/debug.log", "a") as f:
            f.write("PDF: Key takeaways section added successfully\n")

        # Save PDF
        pdf.output(str(file_path))

        with open("/tmp/debug.log", "a") as f:
            f.write(f"PDF: File saved successfully to {file_path}\n")

        download_url = f"{reverse('download-file', kwargs={'filename': filename})}"

        with open("/tmp/debug.log", "a") as f:
            f.write(f"PDF: Download URL generated: {download_url}\n")
            f.write("=== PDF GENERATION SUCCESS ===\n")

        return (True, download_url)
    except Exception as e:
        with open("/tmp/debug.log", "a") as f:
            f.write(f"PDF GENERATION EXCEPTION: {str(e)}\n")
            f.write(f"Exception type: {type(e).__name__}\n")
            f.write("=== PDF GENERATION FAILED ===\n")
        return (False, None)
