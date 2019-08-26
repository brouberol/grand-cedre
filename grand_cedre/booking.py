import datetime
import calendar
import logging

from decimal import Decimal
from grand_cedre.service import get_service
from grand_cedre.pricing import Duration, booking_price, NoMatchingPrice
from grand_cedre.models.contract import Contract
from grand_cedre.models.client import Client


class RoomBooking:
    def __init__(self, start, end, creator_email, title, individual):
        self.start = start
        self.end = end
        self.creator_email = creator_email
        self.title = title
        self.individual = individual
        self._price = None
        self._creator = None

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} "
            f"[{self.creator_email}] - '{self.title}' - {self.start.date()} "
            f"{self._format_time(self.start.time())}->"
            f"{self._format_time(self.end.time())}>"
        )

    def _format_time(self, t):
        return f"{str(t.hour).zfill(2)}h{str(t.minute).zfill(2)}"

    @property
    def duration(self):
        return (self.end - self.start).seconds / 3600

    @property
    def duration_class(self):
        return Duration.from_hour(self.duration)

    @property
    def price(self):
        return self._price

    @property
    def creator(self):
        return self._creator

    @classmethod
    def from_event(cls, event, individual):
        return cls(
            start=datetime.datetime.strptime(
                event["start"]["dateTime"], "%Y-%m-%dT%H:%M:%S+%f:00"
            ),
            end=datetime.datetime.strptime(
                event["end"]["dateTime"], "%Y-%m-%dT%H:%M:%S+%f:00"
            ),
            creator_email=event["creator"]["email"],
            title=event["summary"],
            individual=individual,
        )

    def resolve(self, session):
        self._creator = session.query(Client).filter_by(email=self.creator_email).one()

        try:
            self._price = booking_price(self.duration_class, self.individual)
        except NoMatchingPrice as exc:
            logging.warning(
                f"{self} could not be resolved. Checking if there's an existing contract"
            )

            contract = (
                session.query(Contract)
                .filter(Contract.client == self.creator)
                .filter(Contract.start_date <= datetime.date.today())
                .filter(Contract.end_date >= datetime.date.today())
                .filter(Contract.booking_duration == self.duration)
                .first()
            )
            if contract:
                logging.info(
                    f"Contract found! Using the hourly rate {contract.hourly_rate}"
                )
                self._price = Decimal(contract.hourly_rate) * Decimal(self.duration)
            else:
                raise exc


def start_of_current_month():
    now = datetime.datetime.utcnow()
    monthstart = now.replace(day=1, hour=0, minute=0, second=0)
    return monthstart


def end_of_current_month():
    now = datetime.datetime.utcnow()
    _, last_day = calendar.monthrange(now.year, now.month)
    monthend = now.replace(day=last_day, hour=0, minute=0, second=0)
    return monthend


def list_monthly_bookings(calendar, session):
    out = []
    service = get_service()
    start_of_month = start_of_current_month().isoformat() + "Z"
    end_of_month = end_of_current_month().isoformat() + "Z"
    resp = (
        service.events()
        .list(
            calendarId=calendar["id"],
            timeMin=start_of_month,
            timeMax=end_of_month,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    for event in resp.get("items", []):
        booking = RoomBooking.from_event(event, calendar["metadata"]["individual"])
        booking.resolve(session)
        out.append(booking)
    return out