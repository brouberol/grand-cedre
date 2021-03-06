import datetime
import tempfile
import os

from datetime import date
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
from grand_cedre.web.log import logger


def generate_invoice_per_contract(
    session, upload, parent_id, jinja_env, year=None, month=None
):
    today = date.today()
    if today.month == 1:
        current_year = today.year - 1
        previous_month = 12
    else:
        previous_month = today.month - 1
        current_year = today.year

    start = start_of_month(year=current_year, month=previous_month).date()
    end = end_of_month(year=current_year, month=previous_month).date()

    drive_service = get_drive_service()
    first_upload_done = False

    for i, contract in enumerate(session.query(Contract)):
        if contract.client.is_owner:
            logger.info(
                f"Skipping invoice generation for {contract} as client is the owner"
            )
            continue
        elif contract.client.missing_details():
            logger.warning(
                (
                    f"Skipping invoice generation for contract {contract} "
                    "as its client is missing details"
                )
            )
            continue
        elif contract.type == ContractType.exchange:
            logger.info(f"Skipping exchange contract invoice generation for {contract}")
            continue

        logger.info(f"Generating invoice for {contract} for period {start}->{end}")
        bookings = (
            session.query(DailyBooking)
            .filter(DailyBooking.client_id == contract.client.id)
            .filter(and_(start <= DailyBooking.date, DailyBooking.date <= end))
        ).all()

        if not bookings:
            logger.info(f"No bookings for {contract.client} between {start} and {end}")
            continue

        invoice, created = get_or_create(
            session,
            Invoice,
            defaults={"issued_at": datetime.date.today()},
            contract_id=contract.id,
            period=Invoice.format_period(date=start),
            currency="EURO",
        )
        if created:
            for booking in bookings:
                booking.invoice = invoice
                booking.frozen = True
                session.add(booking)
            session.commit()
            logger.info(f"Invoice for {invoice.total_price}{invoice.symbol} generated")
        else:
            logger.info(f"Invoice {invoice} already was generated")

        if upload:
            if not first_upload_done:
                for folder_name in [
                    current_year,
                    format_date(start, "MMMM", locale="fr_FR").capitalize(),
                ]:
                    parent_id = ensure_drive_folder(
                        folder_name, parent_id, drive_service
                    )
                first_upload_done = True
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
