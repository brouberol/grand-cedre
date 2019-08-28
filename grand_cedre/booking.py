import datetime
import logging

from decimal import Decimal

from grand_cedre.utils import start_of_month, end_of_month
from grand_cedre.service import get_service
from grand_cedre.pricing import Duration, booking_price, NoMatchingPrice
from grand_cedre.models.contract import Contract
from grand_cedre.models.client import Client
from grand_cedre.models.booking import Booking
from grand_cedre.models.room import Room


class RoomBooking:
    def __init__(self, start, end, creator_email, title, link, individual):
        self.start = start
        self.end = end
        self.creator_email = creator_email
        self.title = title
        self.link = link
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
            link=event["htmlLink"],
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

    def to_model(self, session, calendar_id):
        room = session.query(Room).filter_by(calendar_id=calendar_id).one()
        booking = session.query(Booking).filter_by(calendar_link=self.link).first()
        if not booking:
            logging.info(f"Inserting new booking for {self}")
            booking = Booking(
                room=room,
                client=self._creator,
                start_datetime=self.start,
                end_datetime=self.end,
                calendar_link=self.link,
                price=str(self.price),
            )
        else:
            logging.info(f"Updating booking {self}")
            booking.start_datetime = self.start
            booking.end_datetime = self.end
            booking.price = str(self.price)
        return booking


def list_monthly_bookings(calendar, session, start=None, end=None):
    out = []
    service = get_service()
    start = (start or start_of_month()).isoformat() + "Z"
    end = (end or end_of_month()).isoformat() + "Z"
    logging.info(f"Fetching events from {start} to {end}")
    resp = (
        service.events()
        .list(
            calendarId=calendar["id"],
            timeMin=start,
            timeMax=end,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    for event in resp.get("items", []):
        booking = RoomBooking.from_event(event, calendar["metadata"]["individual"])
        booking.resolve(session)
        session.add(booking.to_model(session, calendar["id"]))
        out.append(booking)
    return out
