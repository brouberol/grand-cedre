from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from decimal import Decimal

from grand_cedre.models import PolymorphicBase
from grand_cedre.models.client import Client
from grand_cedre.models.pricing import Pricing
from grand_cedre.pricing import booking_price as compute_booking_price


# Several types of contract:
# - standard: hourly rates apply
# - recurrent: separate rates apply (ex: one whole day every week)
# - exchange: no fees apply
# - flat rate: clients pre-pay for a fixed number of hours,
#   and then freely consume these hours


class Contract(PolymorphicBase):
    __tablename__ = "standard_contracts"
    __table_args__ = (UniqueConstraint("client_id", "start_date"),)
    _type = "standard"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    pricing_id = Column(Integer, ForeignKey("pricings.id"))
    start_date = Column(Date)

    client = relationship("Client", back_populates="contracts")
    pricing = relationship("Pricing", back_populates="contracts")
    type = Column(String(50), nullable=False)

    # This allows us to establish a polymorphic relationship between
    # client and contracts, as contracts can be of several types
    __mapper_args__ = {"polymorphic_identity": "standard"}

    def __str__(self):
        return f"{str(self.client)}: {self.start_date}->{self.end_date}: {self.type}"

    def __repr__(self):
        return f"<{self.__class__.__name__}: {str(self)}>"

    def get_booking_price(self, booking_duration, individual):
        return compute_booking_price(booking_duration, individual)


class OneShotContract(Contract):
    """A recurrent contract apply special fees for recurrent bookings."""

    __tablename__ = "one_shot_contracts"
    __mapper_args__ = {"polymorphic_identity": "recurrent"}
    _type = "recurrent"

    id = Column(Integer, ForeignKey("standard_contracts.id"), primary_key=True)

    def get_booking_price(self, *args, **kwargs):
        pass


class ExchangeContract(Contract):
    """
    An exchange contract represent an exchange of service.

    No fees apply for bookings.
    """

    __tablename__ = "exchange_contracts"
    __mapper_args__ = {"polymorphic_identity": "exchange"}
    _type = "exchange"

    id = Column(Integer, ForeignKey("standard_contracts.id"), primary_key=True)

    def get_booking_price(self, *args, **kwargs):
        return Decimal("0.0")


class FlatRateContract(Contract):
    """A flat rate contract allows a client to pre-pay 40 hours"""

    __tablename__ = "flate_rate_contracts"
    __mapper_args__ = {"polymorphic_identity": "flat_rate"}
    _type = "flat_rate"
    _nb_prepaid_hours = 40
    _price = 360

    id = Column(Integer, ForeignKey("standard_contracts.id"), primary_key=True)
    end_date = Column(Date)
    total_hours = Column(String, nullable=False)
    remaining_hours = Column(String, nullable=False)

    def get_booking_price(self):
        return Decimal(self._price / self._nb_prepaid_hours)

    def add_booking(self, booking_duration):
        # What happens if we go under 0?
        self.remaining_hours = str(
            Decimal(self.remaining_hours) - Decimal(booking_duration)
        )
