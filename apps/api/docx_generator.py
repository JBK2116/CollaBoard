"""
This module handles all the logic
for generating a docx meeting summary
"""

from pathlib import Path
from typing import Any

import docx
from django.urls import reverse

from collaboard import settings


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
    print(data)
    export_path = Path(settings.MEDIA_ROOT) / "exports"
    filename = f"meeting_{meeting_id}.docx"
    file_path = export_path / filename
    author: str | None = data.get("author", None)
    if not author:
        return (False, None)
    doc = docx.Document()
    doc.add_heading(author)
    doc.save(str(file_path))
    return (True, f"{reverse('download-file', kwargs={'filename': filename})}")
