from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from grand_cedre.models import Base


class RoomType:
    individual = "individual"
    collective = "collective"


class Room(Base):

    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    individual = Column(Boolean)
    calendar_id = Column(String, unique=True)

    def __str__(self):
        return self.name

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}: {(str(self))}: individual:{self.individual}>"
        )
