from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from grand_cedre.models import Base
from grand_cedre.models.client import Client


class Contract(Base):
    __tablename__ = "contracts"
    __table_args__ = (
        UniqueConstraint("client_id", "start_date", "end_date", "booking_duration"),
    )

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    start_date = Column(Date)
    end_date = Column(Date)
    booking_duration = Column(Float)
    hourly_rate = Column(String)

    client = relationship("Client", back_populates="contracts")

    def __str__(self):
        return (
            f"{str(self.client)}: {self.start_date}->{self.end_date}:"
            f" {self.booking_duration}h"
        )

    def __repr__(self):
        return f"<{self.__class__.__name__}: {str(self)}>"
