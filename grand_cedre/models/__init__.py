from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

Base.__repr__ = lambda self: f"<{self.__class__.__name__}: {str(self)}>"


class PolymorphicBase(Base):
    __abstract__ = True
    __mapper_args__ = {"polymorphic_on": "type"}

    def __init__(self, *args, **kwargs):
        self.type = self._type
        self.__mapper_args__["polymorphic_identity"] = self._type
        super().__init__(*args, **kwargs)


from .booking import DailyBooking
from .client import Client
from .invoice import Invoice
from .room import Room
from grand_cedre.models.contract import (
    Contract,
    FlatRateContract,
    ExchangeContract,
    OneShotContract,
)
from grand_cedre.models.pricing import (
    IndividualRoomModularPricing,
    CollectiveRoomRegularPricing,
    CollectiveRoomOccasionalPricing,
    FlatRatePricing,
    RecurringPricing,
)
