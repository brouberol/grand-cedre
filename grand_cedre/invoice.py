import datetime
import logging

from sqlalchemy import and_

from grand_cedre.utils import start_of_month, end_of_month, get_or_create
from grand_cedre.models.contract import Contract
from grand_cedre.models.booking import DailyBooking
from grand_cedre.models.invoice import Invoice
from grand_cedre.models.types import ContractType


def generate_invoice_per_contract(session, year=None, month=None):
    start = start_of_month(year, month)
    end = end_of_month(year, month)
    for contract in session.query(Contract):
        if contract.client.is_owner:
            logging.info(
                "Skipping invoice generation for {contract} as client is the owner"
            )
            continue
        elif contract.client.missing_details():
            logging.warning(
                f"Skipping invoice generation for contract {contract} as it's client is missing details"
            )
            continue
        logging.info(f"Generating invoice for {contract} for period {start}->{end}")
        invoice, created = get_or_create(
            session,
            Invoice,
            defaults={"issued_at": datetime.date.today()},
            contract_id=contract.id,
            period=Invoice.format_period(),
            currency="EURO",
        )
        if contract.type == ContractType.standard:
            bookings = (
                session.query(DailyBooking)
                .filter(DailyBooking.client_id == contract.client.id)
                .filter(and_(start <= DailyBooking.date, DailyBooking.date <= end))
            ).all()
            if bookings:

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
