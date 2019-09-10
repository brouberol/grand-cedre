from sqlalchemy import Column, Date, Integer, String

from grand_cedre.models import GrandCedreBase


class Expense(GrandCedreBase):

    __tablename__ = GrandCedreBase.get_table_name("Expense")

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    label = Column(String(255), nullable=False)
    price = Column(String(8), nullable=False)
