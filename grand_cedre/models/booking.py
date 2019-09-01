import logging

from decimal import Decimal

from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, event
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from grand_cedre.models import Base
from grand_cedre.models.room import RoomType
from grand_cedre.models.contract import FlatRateContract, ContractType


class DailyBooking(Base):
    __tablename__ = "daily_bookings"
    __table_args__ = (UniqueConstraint("client_id", "date", "individual"),)

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    date = Column(Date)
    duration_hours = Column(String)
    price = Column(String)
    individual = Column(Boolean)
    frozen = Column(Boolean, default=False)

    client = relationship("Client", back_populates="daily_bookings")
    invoice = relationship("Invoice", back_populates="daily_bookings")

    def __str__(self):
        return (
            f"[{self.client}] - {self.date} - "
            f"{'individual' if self.individual else 'collective'} {self.duration_hours}h"
        )

    def __repr__(self):
        return f"<{self.__class__.__name__}: {(str(self))}: price:{self.price}>"

    @property
    def contract(self):
        room_type = RoomType.individual if self.individual else RoomType.collective
        contracts = [
            contract
            for contract in self.client.contracts
            if contract.room_type.name == room_type
        ]
        if not contracts:
            # raise error?
            pass
        return contracts[0]


def _update_flat_rate_contract_remaining_hours(connection, booking, delete=True):
    log = logging.getLogger("grand-cedre.models.booking")
    remaining_hours = connection.execute(
        (
            f"SELECT remaining_hours FROM {FlatRateContract.__tablename__} "
            f"WHERE id={booking.contract.id}"
        )
    ).first()[0]
    if delete:
        remaining_hours = Decimal(remaining_hours) + Decimal(booking.duration_hours)
        log.info(
            (
                f"Updating {booking.client}'s flat rate contract to "
                f"remaining_hours: {str(remaining_hours)}h after deletion "
                f"of booking {booking}"
            )
        )
    else:
        remaining_hours = Decimal(remaining_hours) - Decimal(booking.duration_hours)
        log.info(
            (
                f"Updating {booking.client}'s flat rate contract to "
                f"remaining_hours: {str(remaining_hours)}h after creation "
                f"of booking {booking}"
            )
        )
    connection.execute(
        (
            f"UPDATE {FlatRateContract.__tablename__} "
            f"SET remaining_hours={str(remaining_hours)} "
            f"WHERE id={booking.contract.id}"
        )
    )


@event.listens_for(DailyBooking, "before_delete")
def before_booking_delete(mapper, connection, target):
    if target.contract.type == ContractType.flat_rate:
        _update_flat_rate_contract_remaining_hours(connection, target, delete=True)


@event.listens_for(DailyBooking, "before_insert")
def before_booking_insert(mapper, connection, target):
    if target.contract.type == ContractType.flat_rate:
        _update_flat_rate_contract_remaining_hours(connection, target, delete=False)
