from sqlalchemy.ext.declarative import declarative_base
from grand_cedre.models.tables import tables

Base = declarative_base()


class GrandCedreBase(Base):
    __abstract__ = True

    @staticmethod
    def get_table_name(model):
        return tables[model]


from .client import Client
from .invoice import Invoice
from .room import Room
from grand_cedre.models.pricing import (
    Pricing,
    CollectiveRoomRegularPricing,
    CollectiveRoomOccasionalPricing,
    FlatRatePricing,
    RecurringPricing,
)
from grand_cedre.models.contract import Contract
from .booking import DailyBooking
