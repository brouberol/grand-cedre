import pickle
import os.path

from googleapiclient.discovery import build


current_dir = os.path.abspath(os.path.dirname(__file__))


def _load_token():
    with open(os.path.join(current_dir, "..", "data", "token.pickle"), "rb") as f:
        return pickle.load(f)


def get_calendar_service():
    return build("calendar", "v3", credentials=_load_token())


def get_drive_service():
    return build("drive", "v3", credentials=_load_token())
