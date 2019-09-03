from sqlalchemy import Column, Integer, String, Boolean

from grand_cedre.models import GrandCedreBase


class Room(GrandCedreBase):

    __tablename__ = GrandCedreBase.get_table_name("Room")
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
