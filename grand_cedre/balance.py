import tempfile

from datetime import date
from babel.dates import format_date

from grand_cedre.utils import (
    get_or_create,
    start_of_month,
    end_of_month,
    ensure_drive_folder,
    ensure_drive_file,
)
from grand_cedre.service import get_drive_service
from grand_cedre.models.balance import BalanceSheet
from grand_cedre.web.log import logger


def insert_last_month_balance_sheet_in_db(session, start_date=None, end_date=None):
    if not all([start_date, end_date]):
        current_year = date.today().year
        previous_month = date.today().month - 1
        start_date = start_of_month(year=current_year, month=previous_month).date()
        end_date = end_of_month(year=current_year, month=previous_month).date()

    balance_sheet, created = get_or_create(
        session, BalanceSheet, start_date=start_date, end_date=end_date
    )
    if created:
        logger.info(f"Creating {repr(balance_sheet)}")
        session.add(balance_sheet)
    return balance_sheet


def upload_balance_sheet(balance_sheet, root_folder_id, session):
    drive = get_drive_service()
    parent = root_folder_id
    for folder_name in [
        str(balance_sheet.start_date.year),
        format_date(balance_sheet.start_date, "MMMM", locale="fr_FR").capitalize(),
    ]:
        parent = ensure_drive_folder(
            name=folder_name, parent_id=parent, drive_service=drive
        )

    with tempfile.TemporaryFile(mode="w", suffix=".csv", encoding="utf-8") as f:
        f.write(balance_sheet.to_csv(session))
        f.flush()
        ensure_drive_file(
            local_filename=f.name,
            remote_filename=balance_sheet.filename(),
            description=f"Bilan financier {balance_sheet}",
            mimetype="text/csv",
            parent_id=parent,
            drive_service=drive,
        )
