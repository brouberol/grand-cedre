import pickle
import os.path

from googleapiclient.discovery import build


current_dir = os.path.abspath(os.path.dirname(__file__))


def get_service():
    with open(os.path.join(current_dir, '..', 'data', 'token.pickle'), 'rb') as f:
        token = pickle.load(f)
    return build('calendar', 'v3', credentials=token)
