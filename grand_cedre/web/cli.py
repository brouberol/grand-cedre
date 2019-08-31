import click
import json
import os

from collections import defaultdict

from . import app
from .db import db

from grand_cedre.models.room import Room
from grand_cedre.pricing import NoMatchingPrice
from grand_cedre.invoice import generate_invoice_per_user
from grand_cedre.booking import import_monthly_bookings


current_dir = os.path.abspath(os.path.dirname(__file__))


@app.cli.command("generate-invoices")
@click.option("--year", type=int)
@click.option("--month", type=int)
def generate_invoices(year, month):
    """Generate an invoice for the current month of the argument month/year"""
    generate_invoice_per_user(db.session, year, month)
    db.session.commit()


@app.cli.command("import-bookings")
@click.option("--year", type=int)
@click.option("--month", type=int)
def import_bookings(year, month):
    """Parse events from the Google calendars and insert them to DB"""
    calendars = json.load(
        open(os.path.join(current_dir, "..", "..", "data", "calendars.json"))
    )
    monthly_bookings = defaultdict(list)

    for calendar in calendars:
        app.logger.info(f"Fetching monthly bookings for calendar {calendar['summary']}")
        bookings = import_monthly_bookings(calendar, db.session, year, month)

        for booking in bookings:
            try:
                app.logger.info(f"{booking} will be billed {booking.price} euro")
            except NoMatchingPrice:
                app.logger.error(f"{booking} could not be priced")
            else:
                monthly_bookings[booking.creator.email].append(booking)

    for user, bookings in monthly_bookings.items():
        total_owed = sum([booking.price for booking in bookings])
        app.logger.info(f"{user} owes a total of {total_owed} ")
    db.session.commit()


@app.cli.command("import-fixtures")
def import_fixtures():
    """Insert fixtures into database"""
    with open(os.path.join(current_dir, "..", "..", "data", "calendars.json")) as dataf:
        calendars = json.load(dataf)

    for calendar in calendars:
        room = Room(
            name=calendar["summary"].split(" - ")[0],
            individual=calendar["metadata"]["individual"],
            calendar_id=calendar["id"],
        )
        app.logger.info(f"Creating room {room}")
        db.session.add(room)
    db.session.commit()
