"""
This module handles all the logic
for generating a pdf meeting summary
"""

from pathlib import Path
from typing import Any

from django.urls import reverse
from fpdf import FPDF

from apps.api import utils

FILE_TYPE: utils.FileTypes = utils.FileTypes.PDF


class MeetingSummaryPDF(FPDF):
    def header(self):
        # Only add header after first page (so title page is clean)
        if self.page_no() > 1:
            self.set_font('Arial', 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, 'Meeting Summary', 0, 1, 'C')
            self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def add_title(self, title_text):
        """Add centered main title"""
        self.set_font('Arial', 'B', 18)
        self.set_text_color(0, 0, 0)
        self.ln(20)  # Top spacing
        self.cell(0, 15, title_text, 0, 1, 'C')
        self.ln(10)
    
    def add_metadata(self, date_text, time_created_text, author_text, description_text):
        """Add meeting metadata section"""
        # Date Created
        self.set_font('Arial', '', 14)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, f'Date Created: {date_text}', 0, 1, 'L')
        self.ln(2)
        
        # Created At
        self.cell(0, 8, f'Created At: {time_created_text}', 0, 1, 'L')
        self.ln(2)
        
        # Director (bold and italic)
        self.set_font('Arial', 'BI', 14)
        self.cell(0, 8, f'Director: {author_text}', 0, 1, 'L')
        self.ln(8)
        
        # Description (centered, smaller font)
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 6, description_text, 0, 'C')
        self.ln(15)
    
    def add_question_section(self, question_text, response_count_text, summary_text):
        """Add a question analysis section"""
        # Check if we need a new page (rough estimation)
        if self.get_y() > 220:  # Near bottom of page
            self.add_page()
        
        # Add some spacing before question
        self.ln(12)
        
        # Question title (centered, bold)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 8, question_text, 0, 'C')
        self.ln(4)
        
        # Response count
        self.set_font('Arial', '', 14)
        self.cell(0, 6, f'Total Responses: {response_count_text}', 0, 1, 'L')
        self.ln(4)
        
        # Summary (centered, justified text)
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 6, summary_text, 0, 'C')
        self.ln(8)
    
    def add_key_takeaways_section(self, key_takeaways):
        """Add key takeaways section on new page"""
        self.add_page()
        
        # Section header
        self.set_font('Arial', 'B', 16)
        self.set_text_color(0, 0, 0)
        self.cell(0, 12, 'Key Takeaways', 0, 1, 'C')
        self.ln(8)
        
        # Add each takeaway as numbered bullet
        for index, text in enumerate(key_takeaways, start=1):
            self.set_font('Arial', 'B', 12)
            # Bullet point with number
            self.cell(15, 8, f'{index}.', 0, 0, 'L')
            
            # Bold "Takeaway X:" label
            self.cell(25, 8, f'Takeaway {index}:', 0, 0, 'L')
            
            # Regular text for the content
            self.set_font('Arial', '', 12)
            
            # Calculate remaining width for text
            remaining_width = self.w - self.l_margin - self.r_margin - 40
            
            # Use multi_cell for wrapping, but position it correctly
            x_pos = self.get_x()
            y_pos = self.get_y()
            
            self.set_xy(x_pos, y_pos)
            self.multi_cell(remaining_width, 6, text, 0, 'L')
            self.ln(4)


def generate_pdf(data: dict[str, Any], meeting_id: str) -> tuple[bool, str | None]:
    """
    Creates a pdf file using the provided data dict.

    Saves the pdf file in `media/exports/meeting_id`

    Returns:
        tuple(bool, str | None, ):
            `bool: represents creation success (False for error occurred, True otherwise)`.             
            `str | None: represents the download url for the newly created file if it was successfully created`

    Example Return:
    ```
    (False, None) -> Error occurred somewhere
    (True, URL(in string format))
    ```

    """

    export_path: Path = utils.get_export_path()
    filename: str = utils.generate_filename(meeting_id=meeting_id, file_type=FILE_TYPE)
    file_path: Path = utils.generate_file_path(
        export_path=export_path, filename=filename
    )

    meeting_metadata: dict[str, Any] | None = utils.get_meeting_metadata(data=data)
    if not meeting_metadata:
        return (False, None)

    questions_analysis_dictionaries: list[dict[str, Any]] | None = (
        utils.get_summarized_meeting_question_analysis(data=data)
    )
    if not questions_analysis_dictionaries:
        return (False, None)

    key_takeaways: list[str] | None = utils.get_summarized_meeting_key_takeaways(
        data=data
    )
    if not key_takeaways:
        return (False, None)

    # NOTE: All data has been validated by this point
    pdf = MeetingSummaryPDF()
    pdf.add_page()

    # TITLE
    title_text = meeting_metadata.get("title", "")
    pdf.add_title(title_text)

    # METADATA
    date_text = meeting_metadata.get("date", "")
    time_created_text = meeting_metadata.get("time_created", "")
    author_text = meeting_metadata.get("author", "")
    description_text = meeting_metadata.get("description", "")
    
    pdf.add_metadata(date_text, time_created_text, author_text, description_text)

    # QUESTION AND RESPONSES
    for question_summary in questions_analysis_dictionaries:
        question_text = question_summary.get("question", "")
        response_count_text = question_summary.get("response_count", "")
        summary_text = question_summary.get("summary", "")
        
        pdf.add_question_section(question_text, response_count_text, summary_text)

    # KEY TAKEAWAYS
    pdf.add_key_takeaways_section(key_takeaways)

    # SAVE PDF
    pdf.output(str(file_path))
    
    return (True, f"{reverse('download-file', kwargs={'filename': filename})}")