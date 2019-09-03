import click
import json
import os

from datetime import date
from decimal import Decimal

from . import app
from .db import db

from grand_cedre.models.room import Room
from grand_cedre.models.pricing import (
    Pricing,
    CollectiveRoomRegularPricing,
    CollectiveRoomOccasionalPricing,
    FlatRatePricing,
    RecurringPricing,
)
from grand_cedre.invoice import generate_invoice_per_user
from grand_cedre.booking import import_monthly_bookings
from grand_cedre.utils import get_or_create

current_dir = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.join(current_dir, "..", "..", "data")


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
@click.option("--pdb", is_flag=True)
@click.option("--no-commit", is_flag=True)
def import_bookings(year, month, pdb, no_commit):
    """Parse events from the Google calendars and insert them to DB"""
    with open(os.path.join(data_dir, "calendars.json")) as f:
        calendars = json.load(f)
    if pdb:
        import pdb

        pdb.set_trace()
    import_monthly_bookings(calendars, db.session, year, month)
    if not no_commit:
        db.session.commit()


def insert_prices_from_file(model, filename):
    with open(os.path.join(data_dir, filename)) as f:
        pricings = json.load(f)
    for interval, price in pricings.items():
        duration_from, duration_to = interval.split("->")
        today = date.today()
        if model == RecurringPricing:
            duration_to = int(Decimal(duration_to) * 8)
            duration_from = int(Decimal(duration_from) * 8)
            pricing, created = get_or_create(
                db.session,
                model,
                defaults={"valid_from": today},
                monthly_price=price,
                duration_from=duration_from,
                duration_to=duration_to,
            )
        else:
            duration_to = int(duration_to) if duration_to else None
            duration_from = int(duration_from)
            pricing, created = get_or_create(
                db.session,
                model,
                defaults={"valid_from": today},
                hourly_price=price,
                duration_from=duration_from,
                duration_to=duration_to,
            )
        if created:
            app.logger.info(f"Creating {pricing.__class__.__name__} {pricing}")


@app.cli.command("import-fixtures")
def import_fixtures():
    """Insert fixtures into database"""
    with open(os.path.join(data_dir, "calendars.json")) as dataf:
        calendars = json.load(dataf)

    for calendar in calendars:
        room, created = get_or_create(
            db.session,
            Room,
            name=calendar["summary"].split(" - ")[0],
            individual=calendar["metadata"]["individual"],
            calendar_id=calendar["id"],
        )
        if created:
            app.logger.info(f"Creating room {room}")
    insert_prices_from_file(
        CollectiveRoomRegularPricing, "collective_regular_pricings.json"
    )
    insert_prices_from_file(
        CollectiveRoomOccasionalPricing, "collective_occasional_pricings.json"
    )
    insert_prices_from_file(Pricing, "individual_modular_pricings.json")
    insert_prices_from_file(RecurringPricing, "individual_recurring_pricings.json")

    with open(os.path.join(data_dir, "flat_rate_pricings.json")) as f:
        prices = json.load(f)

    for price in prices:
        flat_rate_pricing, created = get_or_create(
            db.session,
            FlatRatePricing,
            defaults={"valid_from": date.today()},
            flat_rate=price["flat_rate"],
            prepaid_hours=price["prepaid_hours"],
        )
    if created:
        app.logger.info(
            f"Creating {flat_rate_pricing.__class__.__name__} {flat_rate_pricing}"
        )

    db.session.commit()
