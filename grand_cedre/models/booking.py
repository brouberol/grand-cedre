from decimal import Decimal

from sqlalchemy import Column, Integer, String, Boolean, Date, event
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from grand_cedre.web.log import logger

from grand_cedre.models import GrandCedreBase
from grand_cedre.models.types import RoomType, ContractType


class DailyBooking(GrandCedreBase):
    __tablename__ = GrandCedreBase.get_table_name("DailyBooking")
    __table_args__ = (UniqueConstraint("client_id", "date", "individual"),)

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, GrandCedreBase.fk("Client"))
    invoice_id = Column(Integer, GrandCedreBase.fk("Invoice"))
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
    contract_table = GrandCedreBase.get_table_name("Contract")
    remaining_hours = connection.execute(
        (
            f"SELECT remaining_hours FROM {contract_table} "
            f"WHERE id={booking.contract.id}"
        )
    ).first()[0]
    if delete:
        remaining_hours = Decimal(remaining_hours) + Decimal(booking.duration_hours)
        logger.info(
            (
                f"Updating {booking.client}'s flat rate contract to "
                f"remaining_hours: {str(remaining_hours)}h after deletion "
                f"of booking {booking}"
            )
        )
    else:
        remaining_hours = Decimal(remaining_hours) - Decimal(booking.duration_hours)
        logger.info(
            (
                f"Updating {booking.client}'s flat rate contract to "
                f"remaining_hours: {str(remaining_hours)}h after creation "
                f"of booking {booking}"
            )
        )
    connection.execute(
        (
            f"UPDATE {contract_table} "
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
