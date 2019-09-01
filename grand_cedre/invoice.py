import datetime
import logging

from sqlalchemy import and_

from grand_cedre.utils import start_of_month, end_of_month, get_or_create
from grand_cedre.models.client import Client
from grand_cedre.models.booking import DailyBooking
from grand_cedre.models.invoice import Invoice


def generate_invoice_per_user(session, year=None, month=None):
    start = start_of_month(year, month)
    end = end_of_month(year, month)
    for client in session.query(Client):
        if client.is_owner:
            logging.info(
                "Skipping invoice generation for {client} as (s)he's the owner"
            )
            continue
        elif client.missing_details():
            logging.warning(
                f"Skipping invoice generation for client {client} as it's missing details"
            )
            continue

        logging.info(f"Generating invoice for {client} for period {start}->{end}")
        bookings = (
            session.query(DailyBooking)
            .filter(DailyBooking.client_id == client.id)
            .filter(and_(start <= DailyBooking.date, DailyBooking.date <= end))
        ).all()
        if bookings:

            invoice, created = get_or_create(
                session,
                Invoice,
                defaults={"issued_at": datetime.date.today()},
                client_id=client.id,
                period=Invoice.format_period(),
                currency="EURO",
            )
            if created:
                for booking in bookings:
                    booking.invoice = invoice
                    booking.frozen = True
                    session.add(booking)
                logging.info(
                    f"Invoice for {invoice.total_price}{invoice.symbol} generated"
                )
            else:
                logging.info(f"Invoice {invoice} already was generated")
