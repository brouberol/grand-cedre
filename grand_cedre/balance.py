from datetime import date
import logging

from grand_cedre.utils import get_or_create, start_of_month, end_of_month
from grand_cedre.models.balance import BalanceSheet

logger = logging.getLogger("grand-cedre.balance")


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
