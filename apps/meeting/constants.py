# File: apps/director/meeting/constants.py
"""
Meeting-related constants and enums
"""

from enum import Enum


class MessageTypes:
    """
    Message types used to
    determine the appropriate response
    to a websocket message.
    """

    START_MEETING = "start_meeting"
    END_MEETING = "end_meeting"
    NEXT_QUESTION = "next_question"
    PARTICIPANT_JOINED = "participant_joined"
    PARTICIPANT_LEFT = "participant_left"
    QUESTIONS = "questions"
    SUBMIT_ANSWER = "submit_answer"
    SUBMIT_ERROR = "submit_error"
    INVALID_ANSWER = "invalid_answer"
    UPDATE_NAME = "update_name"


class GroupPrefixes:
    """
    Prefixes used to create and identify group names.
    """

    HOST = "meeting_host_"
    PARTICIPANT = "meeting_"
    MEETING_LOCKED = "meeting_locked_"


class CloseCodes(Enum):
    """
    Codes sent to frontend on
    errors and invalid demands.
    """

    NO_QUESTIONS = ("No questions found", 4004)
    NO_URL_ROUTE = ("Missing or invalid URL route", 4001)
    NO_SESSION = ("Missing or invalid session", 4002)
    AUTH_FAILED = ("Authentication failed", 4003)
    NO_ACCESS_CODE = ("Access code missing or invalid", 4005)
    SUCCESSFUL_CLOSE = ("Connection successfully closed", 1000)

    def __init__(self, message: str, code: int):
        self.message = message
        self.code = code
