import tempfile
import os
import click
import json
import logging

from collections import defaultdict
from weasyprint import HTML
from flask import Flask, abort, make_response, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_babelex import Babel


from grand_cedre.web.admin import register_admin
from grand_cedre.models.booking import Booking
from grand_cedre.models.invoice import Invoice
from grand_cedre.models.room import Room
from grand_cedre.invoice import generate_invoice_per_user
from grand_cedre.booking import import_monthly_bookings
from grand_cedre.pricing import NoMatchingPrice
from grand_cedre.config import Config

current_dir = os.path.abspath(os.path.dirname(__file__))
output_dir = os.path.join(current_dir, "grand_cedre", "output")
template_dir = os.path.join(current_dir, "grand_cedre", "templates")
static_dir = os.path.join(current_dir, "grand_cedre", "static")

app = Flask("grand-cedre", template_folder=template_dir, static_folder=static_dir)
app.config.from_object(Config.from_env())
db = SQLAlchemy(app)
babel = Babel(app)
register_admin(app, db)

# logging configuration
app.logger.setLevel(logging.INFO)
logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)


@babel.localeselector
def get_locale():
    return "fr"


@app.route("/")
def app_index():
    return redirect("/admin")


@app.route("/invoice/<int:invoice_id>/pdf")
def download_invoice_as_pdf(invoice_id):
    invoice = db.session.query(Invoice).get(invoice_id)
    if not invoice:
        abort(404)
    html = invoice.to_html()
    with tempfile.NamedTemporaryFile(
        dir=output_dir, suffix=".html", mode="w"
    ) as tmphtml:
        tmphtml.write(html)
        tmphtml.flush()
        pdf = HTML(tmphtml.name).write_pdf()
    response = make_response(pdf)
    response.headers["Content-type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename={invoice.filename}"
    return response


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
    calendars = json.load(open(os.path.join(current_dir, "data", "calendars.json")))
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
    with open(os.path.join(current_dir, "data", "calendars.json")) as dataf:
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
