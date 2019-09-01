import datetime
import logging

from collections import defaultdict
from sqlalchemy import and_, or_
from grand_cedre.utils import start_of_month, end_of_month, get_or_create
from grand_cedre.service import get_service
from grand_cedre.models.contract import Contract, ContractType
from grand_cedre.models.client import Client
from grand_cedre.models.booking import DailyBooking
from grand_cedre.models.room import RoomType
from grand_cedre.models.pricing import (
    IndividualRoomModularPricing,
    CollectiveRoomRegularPricing,
    CollectiveRoomOccasionalPricing,
    FlatRatePricing,
    RecurringPricing,
)

# Map the contract type and room type to a pricing model
pricing_by_contract_and_room = {
    (ContractType.standard, RoomType.individual): IndividualRoomModularPricing,
    (ContractType.standard, RoomType.collective): CollectiveRoomRegularPricing,
    (ContractType.one_shot, RoomType.collective): CollectiveRoomOccasionalPricing,
    (ContractType.flat_rate, RoomType.individual): FlatRatePricing,
    (ContractType.recurring, RoomType.individual): RecurringPricing,
}

logger = logging.getLogger("grand-cedre.booking")


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

    def resolve(self, session):
        creator = session.query(Client).filter_by(email=self.creator_email).first()
        if not creator:
            creator = Client(email=self.creator_email)
            logging.info(f"Adding client {creator} to DB")
            session.add(creator)
            session.commit()

        self._creator = creator

        logger.debug(f"Checking if there's an existing contract for client {creator}")
        contract = (
            session.query(Contract)
            .filter(Contract.client == self.creator)
            .filter(Contract.start_date <= self.start.date())
            .first()
        )
        if not contract:
            raise NoContractFound


def get_daily_booking_pricing(daily_booking, contract, individual_status, session):
    """
    Get the pricing that was applicable at the time of the booking
    """
    pricing_model = pricing_by_contract_and_room[(contract.type, individual_status)]
    if contract.type == ContractType.flat_rate:
        pricing = (
            session.query(pricing_model)
            .filter(
                and_(
                    pricing_model.valid_from <= daily_booking.date,
                    or_(
                        pricing_model.valid_to.is_(None),
                        pricing_model.valid_to >= daily_booking.date,
                    ),
                )
            )
            .one()
        )
    else:
        pricing = (
            session.query(pricing_model)
            .filter(
                and_(
                    pricing_model.duration_from < daily_booking.duration_hours,
                    pricing_model.duration_to >= daily_booking.duration_hours,
                    pricing_model.valid_from <= daily_booking.date,
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
    # Iterate over daily booking grouped by clients
    for client, daily_bookings_by_date in daily_bookings_by_client.items():

        # Iterate over the client daily bookings grouped by day
        for date, daily_bookings_by_room_type in daily_bookings_by_date.items():

            # Iterate over the client daily bookings grouped by room type
            for (room_type, daily_bookings) in daily_bookings_by_room_type.items():

                logger.info(
                    f"Resolving bookings for {client}, {date}, room_type: {room_type}"
                )
                # Compute the total booking duration for the client/day/room_type
                duration_hours = sum([booking.duration for booking in daily_bookings])
                daily_booking_kwargs = {
                    "client": client,
                    "duration_hours": duration_hours,
                    "individual": room_type == RoomType.individual,
                    "date": daily_bookings[0].day,
                }
                # Get or create the row in DB

                daily_booking, created = get_or_create(
                    session, DailyBooking, **daily_booking_kwargs
                )
                logger.info(f"Bookings: {daily_booking}")

                # Fetch the client contract related to the daily booking
                daily_booking_contract = daily_booking.contract
                logger.info(f"Found contract {daily_booking_contract}")

                # Infer pricing from the contract type and room type
                daily_booking_pricing = get_daily_booking_pricing(
                    daily_booking, daily_booking_contract, room_type, session
                )
                logger.info(f"Found pricing {daily_booking_pricing}")

                # Compute the price from the pricing type
                daily_booking_price = str(
                    daily_booking_pricing.daily_booking_price(daily_booking)
                )
                logger.info(f"Computed price: {daily_booking_price}")
                daily_booking.price = daily_booking_price

                if created:
                    logger.info(f"Created {daily_booking}")
                    # If we're dealing with a flat rate contract, retract consumed
                    # hours from the available credit (the first time only!)
                    if daily_booking_contract.type == ContractType.flat_rate:
                        daily_booking_contract.add_booking(daily_booking)
                        session.add(daily_booking_contract)
                else:
                    logger.info(f"Updating {daily_booking}")

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
        logger.info(
            (
                f"Fetching monthly bookings for calendar {calendar['summary']} "
                "from {start} to {end}"
            )
        )
        for event in resp.get("items", []):
            booking = RoomBooking.from_event(event, calendar["metadata"]["individual"])
            try:
                booking.resolve(session)
            except NoContractFound:
                logger.warning(
                    f"No contract was found for the creator of booking {booking}"
                )
            else:
                room_type = (
                    RoomType.individual if booking.individual else RoomType.collective
                )
                daily_bookings_by_client[booking.creator][booking.day][
                    room_type
                ].append(booking)
    insert_daily_bookings_in_db(daily_bookings_by_client, session)
