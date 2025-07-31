"""
This module handles all the logic
for generating a docx meeting summary
"""

from pathlib import Path
from typing import Any

from django.urls import reverse
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from apps.api import utils

FILE_TYPE: utils.FileTypes = utils.FileTypes.MICROSOFT_WORD


def generate_docx(data: dict[str, Any], meeting_id: str) -> tuple[bool, str | None]:
    """
    Creates a docx file using the provided data dict.

    Saves the docx file in `media/exports/meeting_id`

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
    document = Document()

    # TITLE
    title_text = meeting_metadata.get("title", "")
    title = document.add_heading(text=f"{title_text}", level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER  # Center align
    title.paragraph_format.space_after = Pt(6)

    # TIME DATES
    date_text = meeting_metadata.get("date", "")
    date = document.add_paragraph()
    date_run = date.add_run(text=f"Date Created: {date_text}")
    date_run.font.size = Pt(14)

    time_created_text = meeting_metadata.get("time_created", "")
    time_created = document.add_paragraph()
    time_created_run = time_created.add_run(text=f"Created At: {time_created_text}")
    time_created_run.font.size = Pt(14)

    # AUTHOR
    author_text = meeting_metadata.get("author", "")
    author = document.add_paragraph()
    author_run = author.add_run(text=f"Director: {author_text}")
    author_run.bold = True
    author_run.font.size = Pt(14)
    author_run.italic = True

    # DESCRIPTION
    description_text = meeting_metadata.get("description", "")
    description = document.add_paragraph()
    description.alignment = WD_ALIGN_PARAGRAPH.CENTER
    description_run = description.add_run(text=f"{description_text}")
    description_run.font.size = Pt(12)

    # Add spacing before first question
    spacer = document.add_paragraph()
    spacer.paragraph_format.space_before = Pt(24)

    for question_summary in questions_analysis_dictionaries:
        # Add visual separation between questions (no page breaks)
        spacer = document.add_paragraph()
        spacer.paragraph_format.space_before = Pt(18)
        spacer.paragraph_format.space_after = Pt(6)

        # QUESTION DESCRIPTION
        question_text = question_summary.get("question", "")
        question_description = document.add_heading(text=f"{question_text}", level=2)
        question_description.alignment = WD_ALIGN_PARAGRAPH.CENTER
        question_description.paragraph_format.space_after = Pt(6)

        # RESPONSE COUNT
        response_count_text = question_summary.get("response_count", "")
        question_response_count = document.add_paragraph()
        response_count_run = question_response_count.add_run(
            text=f"Total Responses: {response_count_text}"
        )
        response_count_run.font.size = Pt(14)

        # QUESTION SUMMARY ANALYSIS
        question_summary_text = question_summary.get("summary", "")
        question_summary_analysis = document.add_paragraph()
        question_summary_analysis.alignment = WD_ALIGN_PARAGRAPH.CENTER
        question_summary_run = question_summary_analysis.add_run(
            text=f"{question_summary_text}"
        )
        question_summary_run.font.size = Pt(12)
        question_summary_analysis.paragraph_format.space_after = Pt(12)

    # KEY TAKEAWAYS - Keep page break for this section as it's the executive summary
    document.add_page_break()
    key_takeaways_header = document.add_heading(text="Key Takeaways", level=2)
    key_takeaways_header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    key_takeaways_header.paragraph_format.space_after = Pt(6)

    for index, text in enumerate(key_takeaways, start=1):
        bullet_point = document.add_paragraph(style="List Bullet")
        bullet_point.add_run(f"Takeaway {index}: ").bold = True
        bullet_point.add_run(text)

    document.save(str(file_path))
    return (True, f"{reverse('download-file', kwargs={'filename': filename})}")
