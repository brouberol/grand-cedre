from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy import select, func


from grand_cedre.models import Base


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
        return f"[{self.client}] - {self.date} " f"{self.duration_hours}h"

    def __repr__(self):
        return f"<{self.__class__.__name__}: {(str(self))}: price:{self.price}>"

    @property
    def contract(self):
        individual_status = "individual" if self.individual else "collective"
        contracts = [
            contract
            for contract in self.client.contracts
            if contract.room_type.name == individual_status
        ]
        if not contracts:
            # raise error?
            pass
        return contracts[0]
