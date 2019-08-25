import os.path
import pickle

from google_auth_oauthlib.flow import InstalledAppFlow

current_dir = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.join((current_dir, '..', 'data'))

SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events.readonly']

flow = InstalledAppFlow.from_client_secrets_file(
    os.path.join((data_dir, 'credentials.json')),
    scopes=SCOPES)
creds = flow.run_local_server(port=0)

with open(os.path((data_dir, 'token.pickle')), 'wb') as token:
    pickle.dump(creds, token)
