from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint


from grand_cedre.models import Base
from grand_cedre.pricing import Duration


class Booking(Base):

    __tablename__ = "bookings"
    __table_args__ = (UniqueConstraint("room_id", "start_datetime", "end_datetime"),)

    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("rooms.id"))
    client_id = Column(Integer, ForeignKey("clients.id"))
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    start_datetime = Column(DateTime)
    end_datetime = Column(DateTime)
    calendar_link = Column(String, unique=True)
    price = Column(String)
    frozen = Column(Boolean, default=False)

    client = relationship("Client", back_populates="bookings")
    room = relationship("Room", back_populates="bookings")
    invoice = relationship("Invoice", back_populates="bookings")

    def _format_time(self, t, sep="h"):
        return f"{str(t.hour).zfill(2)}{sep}{str(t.minute).zfill(2)}"

    def __str__(self):
        return (
            f"[{self.client}] - '{self.room}' - {self.start_datetime.date()} "
            f"{self._format_time(self.start_datetime.time())}->"
            f"{self._format_time(self.end_datetime.time())}>"
        )

    def __repr__(self):
        return f"<{self.__class__.__name__}: {(str(self))}: price:{self.price}>"

    @property
    def duration_in_hour(self):
        return (self.end_datetime - self.start_datetime).seconds / 3600.0

    @property
    def duration(self):
        return Duration.from_hour(self.duration_in_hour)
