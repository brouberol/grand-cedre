import datetime
import logging

from collections import defaultdict
from sqlalchemy import and_, or_
from grand_cedre.utils import start_of_month, end_of_month
from grand_cedre.service import get_service
from grand_cedre.models.contract import Contract
from grand_cedre.models.client import Client
from grand_cedre.models.booking import DailyBooking
from grand_cedre.models.pricing import (
    IndividualRoomModularPricing,
    CollectiveRoomRegularPricing,
    CollectiveRoomOccasionalPricing,
    FlatRatePricing,
    RecurringPricing,
)


pricing_by_contract_and_room = {
    ("standard", "individual"): IndividualRoomModularPricing,
    ("standard", "collective"): CollectiveRoomRegularPricing,
    ("one_shot", "collective"): CollectiveRoomOccasionalPricing,
    ("flat_rate", "individual"): FlatRatePricing,
    ("recurring", "individual"): RecurringPricing,
}


class NoContractFound(Exception):
    pass


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
    def day(self):
        return self.start.date()

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

    def price_from_contract(self, contract):
        if contract.type in ("standard", "recurrent", "exchange"):
            return contract.get_booking_price()

    def resolve(self, session):
        creator = session.query(Client).filter_by(email=self.creator_email).first()
        if not creator:
            creator = Client(email=self.creator_email)
            logging.info(f"Adding client {creator} to DB")
            session.add(creator)
            session.commit()

        self._creator = creator

        logging.debug(f"Checking if there's an existing contract for client {creator}")
        contract = (
            session.query(Contract)
            .filter(Contract.client == self.creator)
            .filter(Contract.start_date <= self.start.date())
            .first()
        )
        if not contract:
            raise NoContractFound


def get_daily_booking_pricing(daily_booking, contract, individual_status, session):
    pricing_model = pricing_by_contract_and_room[(contract.type, individual_status)]
    pricing = (
        session.query(pricing_model)
        .filter(
            and_(
                pricing_model.duration_from < daily_booking.duration_hours,
                pricing_model.duration_to >= daily_booking.duration_hours,
                or_(
                    pricing_model.valid_to.is_(None),
                    pricing_model.valid_to >= daily_booking.date,
                ),
            )
        )
        .one()
    )
    return pricing


def insert_daily_bookings_in_db(daily_bookings_by_client, session):
    for client, daily_bookings_by_date in daily_bookings_by_client.items():
        for date, daily_bookings_by_room_type in daily_bookings_by_date.items():
            for (
                individual_status,
                daily_bookings,
            ) in daily_bookings_by_room_type.items():
                individual = True if individual_status == "individual" else False
                duration_hours = sum([booking.duration for booking in daily_bookings])
                daily_booking = DailyBooking(
                    client=client,
                    duration_hours=duration_hours,
                    individual=individual,
                    date=daily_bookings[0].day,
                )
                daily_booking_contract = daily_booking.contract
                daily_booking_pricing = get_daily_booking_pricing(
                    daily_booking, daily_booking_contract, individual_status, session
                )
                daily_booking.price = str(
                    daily_booking_pricing.daily_booking_price(daily_booking)
                )
                if daily_booking_contract.type == "flat_rate":
                    daily_booking_contract.add_booking(daily_booking)
                    session.add(daily_booking_contract)
                session.add(daily_booking)


def import_monthly_bookings(calendars, session, year=None, month=None):
    daily_bookings_by_client = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    service = get_service()
    start = start_of_month(year, month).isoformat() + "Z"
    end = end_of_month(year, month).isoformat() + "Z"
    for calendar in calendars:
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
        logging.info(
            f"Fetching monthly bookings for calendar {calendar['summary']} from {start} to {end}"
        )
        for event in resp.get("items", []):
            booking = RoomBooking.from_event(event, calendar["metadata"]["individual"])
            try:
                booking.resolve(session)
            except NoContractFound:
                logging.warning(
                    f"No contract was found for the creator of booking {booking}"
                )
            else:
                subsection = "individual" if booking.individual else "collective"
                daily_bookings_by_client[booking.creator][booking.day][
                    subsection
                ].append(booking)
    insert_daily_bookings_in_db(daily_bookings_by_client, session)
