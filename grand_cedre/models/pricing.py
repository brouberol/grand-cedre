from decimal import Decimal

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr

from grand_cedre.models import Base


class Pricing(Base):
    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)
    duration_from = Column(Integer, nullable=False)
    duration_to = Column(Integer, nullable=True)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)

    @declared_attr
    def __tablename__(cls):
        if cls.__name__ == "Pricing":
            return "pricings"
        return "pricings_" + cls._type.lower()

    @declared_attr
    def __mapper_args__(cls):
        if cls.__name__ == "Pricing":
            return {"polymorphic_on": "type", "polymorphic_identity": "Pricing"}
        return {"polymorphic_identity": cls._type}

    def __str__(self):
        return (
            f"{self.type}: ] {self.duration_from}h -> {self.duration_to}h ] "
            f"{self.hourly_price}e"
        )


class HourlyPricing:
    def daily_booking_price(self, daily_booking):
        return Decimal(self.hourly_price) * Decimal(daily_booking.duration_hours)


class IndividualRoomModularPricing(HourlyPricing, Pricing):

    _type = "individual_modular"

    id = Column(Integer, ForeignKey("pricings.id"), primary_key=True)
    hourly_price = Column(String(8), nullable=False)


class CollectiveRoomRegularPricing(HourlyPricing, Pricing):

    _type = "collective_regular"

    id = Column(Integer, ForeignKey("pricings.id"), primary_key=True)
    hourly_price = Column(String(8), nullable=False)


class CollectiveRoomOccasionalPricing(HourlyPricing, Pricing):

    _type = "collective_occasional"

    id = Column(Integer, ForeignKey("pricings.id"), primary_key=True)
    hourly_price = Column(String(8), nullable=False)


class FlatRatePricing(Pricing):

    _type = "flat_rate"

    id = Column(Integer, ForeignKey("pricings.id"), primary_key=True)
    flat_rate = Column(String(8), nullable=False)
    prepaid_hours = Column(Integer, nullable=False)

    def __str__(self):
        return (
            f"{self.type}: ]{self.duration_from}h->{self.duration_to}h] "
            f"{self.prepaid_hours}h - {self.flat_rate}e"
        )

    def daily_booking_price(self, daily_booking):
        return Decimal("0.0")


class RecurringPricing(Pricing):

    _type = "recurring"

    id = Column(Integer, ForeignKey("pricings.id"), primary_key=True)
    monthly_price = Column(String(8), nullable=False)

    def __str__(self):
        return (
            f"{self.type}: ]{self.duration_from}d->{self.duration_to}d] "
            f"{self.monthly_price}e"
        )

    def daily_booking_price(self, daily_booking):
        return Decimal("0.0")
