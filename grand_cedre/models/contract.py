from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.types import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from decimal import Decimal
from enum import Enum

from grand_cedre.models import PolymorphicBase
from grand_cedre.models.client import Client
from grand_cedre.models.pricing import Pricing


class RoomType(Enum):
    individual = "Cabinet"
    collective = "Salle collective"

    def __str__(self):
        return self.name


class ContractType:
    standard = "standard"
    one_shot = "one_shot"
    exchange = "exchange"
    recurring = "recurring"
    flat_rate = "flat_rate"


class ContractTypeEnum(Enum):
    standard = "Standard"
    one_shot = "Réservation occasionelle"
    exchange = "Échange"
    recurring = "Occupation récurrente"
    flat_rate = "Forfait"


class Contract(PolymorphicBase):
    """
    A standard contract for a given room type (individual or not),
    allowing a client to book when they need.
    """

    __tablename__ = "standard_contracts"
    __table_args__ = (UniqueConstraint("client_id", "start_date", "room_type"),)
    _type = ContractType.standard

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    start_date = Column(Date)
    room_type = Column(SQLEnum(RoomType))

    client = relationship("Client", back_populates="contracts")
    type = Column(String(50), nullable=False)

    # This allows us to establish a polymorphic relationship between
    # client and contracts, as contracts can be of several types
    __mapper_args__ = {"polymorphic_identity": ContractType.standard}

    def __str__(self):
        return f"{str(self.client)}: {self.start_date}: {self.type}:{self.room_type}"

    def ack_booking(self, booking_duration):
        # What happens if we go under 0?
        if self._type == ContractType.flat_rate:
            self.remaining_hours = str(
                Decimal(self.remaining_hours) - Decimal(booking_duration)
            )


class OneShotContract(Contract):
    """A contract allowing a client to book a room of a given type once"""

    __tablename__ = "one_shot_contracts"
    __mapper_args__ = {"polymorphic_identity": ContractType.one_shot}
    _type = ContractType.one_shot

    id = Column(Integer, ForeignKey("standard_contracts.id"), primary_key=True)


class ExchangeContract(Contract):
    """
    An exchange contract represent an exchange of service.

    No fees apply for bookings.
    """

    __tablename__ = "exchange_contracts"
    __mapper_args__ = {"polymorphic_identity": ContractType.exchange}
    _type = ContractType.exchange

    id = Column(Integer, ForeignKey("standard_contracts.id"), primary_key=True)

    def get_booking_price(self, *args, **kwargs):
        return Decimal("0.0")


class FlatRateContract(Contract):
    """A flat rate contract allows a client to pre-pay a given number of hours"""

    __tablename__ = "flate_rate_contracts"
    __mapper_args__ = {"polymorphic_identity": ContractType.flat_rate}
    _type = ContractType.flat_rate
    _nb_prepaid_hours = 40
    _price = 360

    id = Column(Integer, ForeignKey("standard_contracts.id"), primary_key=True)
    end_date = Column(Date)
    total_hours = Column(String, nullable=False)
    remaining_hours = Column(String, nullable=False)


class RecurringContract(Contract):
    """
    A recurring contract allows a client to regularly book rooms
    for preferential prices

    """

    __tablename__ = "recurring_contracts"
    __mapper_args__ = {"polymorphic_identity": ContractType.recurring}
    _type = ContractType.recurring

    id = Column(Integer, ForeignKey("standard_contracts.id"), primary_key=True)
