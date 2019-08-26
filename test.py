import json
import logging

from collections import defaultdict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from grand_cedre.booking import list_monthly_bookings
from grand_cedre.pricing import NoMatchingPrice


engine = create_engine("sqlite:///data/data.db")
Session = sessionmaker(bind=engine)


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("grand-cedre-billing")
    logger.setLevel(logging.INFO)
    logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)
    return logger


def main():
    logger = setup_logging()
    calendars = json.load(open("./data/calendars.json"))
    monthly_bookings = defaultdict(list)

    session = Session()
    for calendar in calendars:
        logger.info(f"Fectching monthly bookings for calendar {calendar['summary']}")
        bookings = list_monthly_bookings(calendar, session=session)

        for booking in bookings:
            try:
                logger.info(f"{booking} will be billed {booking.price} euro")
            except NoMatchingPrice:
                logger.error(f"{booking} could not be priced")
            else:
                monthly_bookings[booking.creator.email].append(booking)

    for user, bookings in monthly_bookings.items():
        total_owed = sum([booking.price for booking in bookings])
        logger.info(f"{user} owes a total of {total_owed} ")


if __name__ == "__main__":
    main()
