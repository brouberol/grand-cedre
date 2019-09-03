from decimal import Decimal

from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import ConcreteBase

from grand_cedre.models import GrandCedreBase


class Pricing(GrandCedreBase):

    __tablename__ = GrandCedreBase.get_table_name("Pricing")

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False, default="individual_modular")
    duration_from = Column(Integer, nullable=False)
    duration_to = Column(Integer, nullable=True)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)
    hourly_price = Column(String(8), nullable=False)


# class HourlyPricing:
#     def daily_booking_price(self, daily_booking):
#         return (
#             Decimal(self.hourly_price) * Decimal(daily_booking.duration_hours)
#         ).quantize(Decimal("1.00"))
# def __str__(self):
#     if self.duration_to:
#         interval = f"] {self.duration_from}h -> {self.duration_to}h ]"
#     else:
#         interval = f"] {self.duration_from}h -> + ]"
#     return f"{self.type}: {interval}: {self.hourly_price}e"


class CollectiveRoomRegularPricing(GrandCedreBase):

    __tablename__ = GrandCedreBase.get_table_name("CollectiveRoomRegularPricing")

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False, default="collective_regular")
    duration_from = Column(Integer, nullable=False)
    duration_to = Column(Integer, nullable=True)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)
    hourly_price = Column(String(8), nullable=False)


class CollectiveRoomOccasionalPricing(GrandCedreBase):

    __tablename__ = GrandCedreBase.get_table_name("CollectiveRoomOccasionalPricing")

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False, default="collective_occasional")
    duration_from = Column(Integer, nullable=False)
    duration_to = Column(Integer, nullable=True)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)
    hourly_price = Column(String(8), nullable=False)


class FlatRatePricing(GrandCedreBase):

    __tablename__ = GrandCedreBase.get_table_name("FlatRatePricing")

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False, default="flat_rate")
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)
    flat_rate = Column(String(8), nullable=False)
    prepaid_hours = Column(Integer, nullable=False)

    contracts = relationship("Contract", back_populates="flat_rate_pricing")

    def __str__(self):
        return f"{self.prepaid_hours}h - {self.flat_rate}e"

    def daily_booking_price(self, daily_booking):
        return Decimal("0.00")


class RecurringPricing(GrandCedreBase):

    __tablename__ = GrandCedreBase.get_table_name("RecurringPricing")

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False, default="recurring")
    duration_from = Column(Integer, nullable=False)
    duration_to = Column(Integer, nullable=True)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)
    monthly_price = Column(String(8), nullable=False)

    def __str__(self):
        return (
            f"{self.type}: ]{self.duration_from}d->{self.duration_to}d] "
            f"{self.monthly_price}e"
        )

    def daily_booking_price(self, daily_booking):
        return Decimal("0.00")
