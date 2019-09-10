from decimal import Decimal

from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import relationship

from grand_cedre.models import GrandCedreBase
from grand_cedre.models.types import PricingType


class BasePricing:
    def format_interval(self):
        if self.duration_to:
            return f"] {self.duration_from}h -> {self.duration_to}h ]"
        else:
            return f"] {self.duration_from}h -> + ]"


class HourlyPricing(BasePricing):
    def __str__(self):
        return f"{self.type}: {self.format_interval()}: {self.hourly_price}€/h"

    def daily_booking_price(self, daily_booking):
        return (
            Decimal(self.hourly_price) * Decimal(daily_booking.duration_hours)
        ).quantize(Decimal("1.00"))


class MonthlyPricing(BasePricing):
    def __str__(self):
        return f"{self.type}: {self.format_interval()}: {self.monthly_price}€/mois"


class FreePricing(BasePricing):
    @staticmethod
    def daily_booking_price(daily_booking):
        return Decimal("0.00")


class Pricing(HourlyPricing, GrandCedreBase):

    __tablename__ = GrandCedreBase.get_table_name("Pricing")

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False, default=PricingType.individual_modular)
    duration_from = Column(Integer, nullable=False)
    duration_to = Column(Integer, nullable=True)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)
    hourly_price = Column(String(8), nullable=False)


class CollectiveRoomRegularPricing(HourlyPricing, GrandCedreBase):

    __tablename__ = GrandCedreBase.get_table_name("CollectiveRoomRegularPricing")

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False, default=PricingType.collective_regular)
    duration_from = Column(Integer, nullable=False)
    duration_to = Column(Integer, nullable=True)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)
    hourly_price = Column(String(8), nullable=False)


class CollectiveRoomOccasionalPricing(HourlyPricing, GrandCedreBase):

    __tablename__ = GrandCedreBase.get_table_name("CollectiveRoomOccasionalPricing")

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False, default=PricingType.collective_occasional)
    duration_from = Column(Integer, nullable=False)
    duration_to = Column(Integer, nullable=True)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)
    hourly_price = Column(String(8), nullable=False)


class FlatRatePricing(FreePricing, GrandCedreBase):

    __tablename__ = GrandCedreBase.get_table_name("FlatRatePricing")

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False, default=PricingType.flat_rate)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)
    flat_rate = Column(String(8), nullable=False)
    prepaid_hours = Column(Integer, nullable=False)

    contracts = relationship("Contract", back_populates="flat_rate_pricing")

    def __str__(self):
        return f"{self.prepaid_hours}h - {self.flat_rate}€"


class RecurringPricing(MonthlyPricing, FreePricing, GrandCedreBase):

    __tablename__ = GrandCedreBase.get_table_name("RecurringPricing")

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False, default=PricingType.recurring)
    duration_from = Column(Integer, nullable=False)
    duration_to = Column(Integer, nullable=True)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)
    monthly_price = Column(String(8), nullable=False)

    contracts = relationship("Contract", back_populates="recurring_pricing")
