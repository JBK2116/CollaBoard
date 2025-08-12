import os
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from collaboard import settings


# Current Cron Job: 0 * * * * cd /home/jovkb/Projects/collaboard/ && /home/jovkb/.local/bin/pipenv run python manage.py cleanup_media >> /tmp/cleanup.log 2>&1
class Command(BaseCommand):
    help = "Delete all files in the `media/exports/` directory"

    def add_arguments(self, parser: CommandParser) -> None:
        # NOTE: Add additional command arguments here
        return super().add_arguments(parser)

    def handle(self, *args: Any, **options: Any) -> str | None:
        self.cleanup_media()

    def cleanup_media(self) -> None:
        """
        Deletes all the files in the `media/exports/` directory
        """
        directory: Path = settings.MEDIA_ROOT / "exports"
        if not directory.exists():
            print(f"Path: {directory} not found")
        for file in directory.iterdir():
            os.remove(file)
