import click
import json
import os

from datetime import datetime
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
from grand_cedre.invoice import generate_invoice_per_contract
from grand_cedre.booking import import_monthly_bookings
from grand_cedre.balance import (
    insert_last_month_balance_sheet_in_db,
    upload_balance_sheet,
)
from grand_cedre.utils import get_or_create

current_dir = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.join(current_dir, "..", "..", "data")


def parse_date(date_str):
    if date_str:
        return datetime.strptime(date_str, "%Y-%m-%d").date()


@app.cli.command("generate-invoices")
@click.option("--year", type=int)
@click.option("--month", type=int)
@click.option("--no-commit", is_flag=True)
@click.option("--no-upload", is_flag=True)
@click.option("--pdb", is_flag=True)
def generate_invoices(year, month, no_commit, no_upload, pdb):
    """Generate invoices for the argument month/year period"""
    if pdb:
        import pdb

        pdb.set_trace()
    drive_data = json.load(open(os.path.join(data_dir, "drive.json")))
    parent_id = drive_data["base_folder"]["id"]
    generate_invoice_per_contract(
        session=db.session,
        year=year,
        month=month,
        upload=not no_upload,
        parent_id=parent_id,
        jinja_env=app.jinja_env,
    )
    if not no_commit:
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
    for pricing_data in pricings:
        for interval, price in pricing_data["prices"].items():
            duration_from, duration_to = interval.split("->")
            if model == RecurringPricing:
                duration_to = int(float(duration_to) * 60)
                duration_from = int(float(duration_from) * 60)
                pricing, created = get_or_create(
                    db.session,
                    model,
                    defaults={
                        "valid_from": parse_date(pricing_data["valid_from"]),
                        "valid_to": parse_date(pricing_data["valid_to"]),
                    },
                    monthly_price=price,
                    duration_from=duration_from,
                    duration_to=duration_to,
                )
            else:
                duration_to = int(float(duration_to) * 60) if duration_to else None
                duration_from = int(float(duration_from) * 60)
                pricing, created = get_or_create(
                    db.session,
                    model,
                    defaults={
                        "valid_from": parse_date(pricing_data["valid_from"]),
                        "valid_to": parse_date(pricing_data["valid_to"]),
                    },
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
            defaults={
                "valid_from": parse_date(price["valid_from"]),
                "valid_to": parse_date(price["valid_to"]),
            },
            flat_rate=price["flat_rate"],
            prepaid_hours=price["prepaid_hours"],
        )
    if created:
        app.logger.info(
            f"Creating {flat_rate_pricing.__class__.__name__} {flat_rate_pricing}"
        )

    db.session.commit()


@app.cli.command("create-balance-sheet")
@click.option("--start-date")
@click.option("--end-date")
@click.option("--no-upload", is_flag=True)
def create_last_month_balance_sheet(start_date, end_date, no_upload):
    """Create a balance sheet for the argument period (or last month)"""
    start_date = (
        datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    )
    end_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
    sheet = insert_last_month_balance_sheet_in_db(db.session, start_date, end_date)
    db.session.commit()
    if not no_upload:
        app.logger.info("Uploading balance sheet to Drive")
        drive_data = json.load(open(os.path.join(data_dir, "drive.json")))
        try:
            upload_balance_sheet(sheet, drive_data["base_folder"]["id"], db.session)
        except OSError:
            pass
