from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from grand_cedre.models import Base
from grand_cedre.models.client import Client


# Several types of contract:
# - standard: hourly rates apply
# - recurrent: separate rates apply (ex: one whole day every week)
# - exchange: no fees apply
# - flat rate: clients pre-pay for a fixed number of hours,
#   and then freely consume these hours


class Contract(Base):
    __tablename__ = "standard_contracts"
    __table_args__ = (UniqueConstraint("client_id", "start_date", "end_date"),)
    _type = "standard"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    start_date = Column(Date)
    end_date = Column(Date)
    client = relationship("Client", back_populates="contracts")
    type = Column(String(50), nullable=False)

    # This allows us to establish a polymorphic relationship between
    # client and contracts, as contracts can be of several types
    __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "standard"}

    def __init__(self, *args, **kwargs):
        self.type = self._type
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f"{str(self.client)}: {self.start_date}->{self.end_date}: {self.type}"

    def __repr__(self):
        return f"<{self.__class__.__name__}: {str(self)}>"


class RecurrentContract(Contract):
    """A recurrent contract apply special fees for recurrent bookings."""

    __tablename__ = "recurrent_contracts"
    __mapper_args__ = {"polymorphic_identity": "recurrent"}
    _type = "recurrent"

    id = Column(Integer, ForeignKey("standard_contracts.id"), primary_key=True)
    booking_price = Column(String, nullable=False)


class ExchangeContract(Contract):
    """
    An exchange contract represent an exchange of service.

    No fees apply for bookings.
    """

    __tablename__ = "exchange_contracts"
    __mapper_args__ = {"polymorphic_identity": "exchange"}
    _type = "exchange"

    id = Column(Integer, ForeignKey("standard_contracts.id"), primary_key=True)


class FlatRateContract(Contract):
    """A flat rate contract allows a client to pre-pay a given number of hours"""

    __tablename__ = "flate_rate_contracts"
    __mapper_args__ = {"polymorphic_identity": "flat_rate"}
    _type = "flat_rate"

    id = Column(Integer, ForeignKey("standard_contracts.id"), primary_key=True)
    total_hours = Column(String, nullable=False)
    remaining_hours = Column(String, nullable=False)
    hourly_rate = Column(String, nullable=False)
