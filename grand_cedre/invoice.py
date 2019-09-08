import datetime
import logging
import tempfile
import os

from sqlalchemy import and_
from babel.dates import format_date

from grand_cedre.utils import (
    get_or_create,
    start_of_month,
    end_of_month,
    ensure_drive_folder,
    ensure_drive_file,
)
from grand_cedre.service import get_drive_service
from grand_cedre.models.contract import Contract
from grand_cedre.models.booking import DailyBooking
from grand_cedre.models.invoice import Invoice
from grand_cedre.models.types import ContractType


def generate_invoice_per_contract(
    session, upload, parent_id, jinja_env, year=None, month=None
):
    start = start_of_month(year, month)
    end = end_of_month(year, month)
    drive_service = get_drive_service()
    for i, contract in enumerate(session.query(Contract)):
        if contract.client.is_owner:
            logging.info(
                "Skipping invoice generation for {contract} as client is the owner"
            )
            continue
        elif contract.client.missing_details():
            logging.warning(
                (
                    f"Skipping invoice generation for contract {contract} "
                    "as its client is missing details"
                )
            )
            continue
        elif contract.type == ContractType.exchange:
            logging.info("Skipping exchange contract invoice generation for {contract}")
        logging.info(f"Generating invoice for {contract} for period {start}->{end}")
        invoice, created = get_or_create(
            session,
            Invoice,
            defaults={"issued_at": datetime.date.today()},
            contract_id=contract.id,
            period=Invoice.format_period(),
            currency="EURO",
        )
        bookings = (
            session.query(DailyBooking)
            .filter(DailyBooking.client_id == contract.client.id)
            .filter(and_(start <= DailyBooking.date, DailyBooking.date <= end))
        ).all()
        if created:
            for booking in bookings:
                booking.invoice = invoice
                booking.frozen = True
                session.add(booking)
            logging.info(f"Invoice for {invoice.total_price}{invoice.symbol} generated")
        else:
            logging.info(f"Invoice {invoice} already was generated")

        if upload:
            if i == 0:
                for folder_name in [
                    invoice.issued_at.year,
                    format_date(invoice.issued_at, "MMMM", locale="fr_FR").capitalize(),
                ]:
                    parent_id = ensure_drive_folder(
                        folder_name, parent_id, drive_service
                    )
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(invoice.to_pdf(jinja_env))
        ensure_drive_file(
            local_filename=f.name,
            remote_filename=invoice.filename,
            description=f"Facture - {invoice.contract.client.full_name}",
            mimetype="application/pdf",
            parent_id=parent_id,
            drive_service=drive_service,
        )
        os.unlink(f.name)
