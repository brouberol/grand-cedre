import datetime
import logging

from grand_cedre.utils import start_of_current_month, end_of_current_month
from grand_cedre.models.client import Client
from grand_cedre.models.booking import Booking
from grand_cedre.models.invoice import Invoice


def generate_invoice_per_user(session):
    start, end = start_of_current_month(), end_of_current_month()
    for client in session.query(Client):
        if client.is_owner:
            logging.info(
                "Skipping invoice generation for {client} as (s)he's the owner"
            )
            continue
        logging.info(f"Generating invoice for {client} for period {start}->{end}")
        bookings = (
            session.query(Booking)
            .filter(Booking.client_id == client.id)
            .filter(Booking.start_datetime >= start)
            .filter(Booking.end_datetime <= end)
        ).all()
        if bookings:

            invoice = (
                session.query(Invoice)
                .filter_by(client_id=client.id, period=Invoice.format_period())
                .first()
            )
            if not invoice:
                invoice = Invoice(
                    client_id=client.id,
                    issued_at=datetime.date.today(),
                    currency="EURO",
                    period=Invoice.format_period(),
                )
                session.add(invoice)
                for booking in bookings:
                    booking.invoice = invoice
                    booking.frozen = True
                    session.add(booking)
                logging.info(
                    f"Invoice for {invoice.total_price}{invoice.symbol} generated"
                )
            else:
                logging.info(f"Invoice {invoice} already was generated")
