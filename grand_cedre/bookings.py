import datetime
import calendar

from grand_cedre.service import get_service
from grand_cedre.prices import Duration, booking_price


class RoomBooking:

    def __init__(self, start, end, creator, title, individual):
        self.start = start
        self.end = end
        self.creator = creator
        self.title = title
        self.individual = individual


    def __repr__(self):
        return ((
            f"<{self.__class__.__name__} "
            f"{self.title} - {self.start.date()} "
            f"{self.start.time().replace(second=0, microsecond=0)}->"
            f"{self.end.time().replace(second=0, microsecond=0)}>"
        ))

    @property
    def duration(self):
        return (self.end - self.start).seconds / 3600

    @property
    def duration_class(self):
        return Duration.from_hour(self.duration)

    @property
    def price(self):
        return booking_price(self.duration_class, self.individual)

    @classmethod
    def from_event(cls, event, individual):
        return cls(
            start=datetime.datetime.strptime(
                event['start']['dateTime'], "%Y-%m-%dT%H:%M:%S+%f:00"),
            end=datetime.datetime.strptime(
                event['end']['dateTime'], "%Y-%m-%dT%H:%M:%S+%f:00"),
            creator=event['creator']['email'],
            title=event['summary'],
            individual=individual)


def start_of_current_month():
    now = datetime.datetime.utcnow()
    monthstart = now.replace(day=1, hour=0, minute=0, second=0)
    return monthstart


def end_of_current_month():
    now = datetime.datetime.utcnow()
    _, last_day = calendar.monthrange(now.year, now.month)
    monthend = now.replace(day=last_day, hour=0, minute=0, second=0)
    return monthend


def list_monthly_bookings(calendar_id):
    service = get_service()
    start_of_month = start_of_current_month().isoformat() + 'Z'
    end_of_month = end_of_current_month().isoformat() + 'Z'
    resp = service.events().list(
        calendarId=calendar_id,
        timeMin=start_of_month,
        timeMax=end_of_month,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return [
        RoomBooking.from_event(event, individual=True)
        for event in resp.get('items', [])]
