import os
import sys

current_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, parent_dir)

import json
import logging
import argparse

from collections import defaultdict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from grand_cedre.booking import list_monthly_bookings
from grand_cedre.pricing import NoMatchingPrice
from grand_cedre.utils import start_of_month, end_of_month


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


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int)
    parser.add_argument("--month", type=int)
    return parser.parse_args()


def main():
    args = parse_args()
    logger = setup_logging()
    calendars = json.load(open("./data/calendars.json"))
    monthly_bookings = defaultdict(list)

    session = Session()
    for calendar in calendars:
        logger.info(f"Fetching monthly bookings for calendar {calendar['summary']}")
        if args.year and args.month:
            start = start_of_month(args.year, args.month)
            end = end_of_month(args.year, args.month)
            bookings = list_monthly_bookings(calendar, session, start, end)
        else:
            bookings = list_monthly_bookings(calendar, session)

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

    session.commit()
    session.close()


if __name__ == "__main__":
    main()