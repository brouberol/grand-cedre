import csv

from io import StringIO
from decimal import Decimal
from sqlalchemy import Column, Date, Integer
from sqlalchemy.schema import UniqueConstraint

from grand_cedre.models import GrandCedreBase
from grand_cedre.models.invoice import Invoice
from grand_cedre.models.expense import Expense


class BalanceSheet(GrandCedreBase):
    __tablename__ = GrandCedreBase.get_table_name("BalanceSheet")
    __table_args__ = (UniqueConstraint("start_date", "end_date"),)

    id = Column(Integer, primary_key=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {(str(self))}>"

    def __str__(self):
        return f"{self.start_date} - {self.end_date}"

    def filename(self, extension="csv"):
        return f"bilan-{self.start_date}-{self.end_date}.{extension}"

    def to_csv(self, session):
        csvfile = StringIO()
        invoices = (
            session.query(Invoice)
            .filter(Invoice.payed_at.isnot(None))
            .filter(Invoice.payed_at >= self.start_date)
            .filter(Invoice.payed_at <= self.end_date)
        ).all()
        invoice_total = sum([invoice.total_price for invoice in invoices])

        csvwriter = csv.writer(csvfile)
        invoice_headers = [
            "# Facture",
            "Client",
            "Période",
            "Total",
            "Date d'encaissement",
            "# Chèque",
            "# Virement",
        ]
        csvwriter.writerow(invoice_headers)
        for invoice in invoices:
            csvwriter.writerow(
                [
                    invoice.number,
                    invoice.contract.client.full_name,
                    invoice.period,
                    str(invoice.total_price),
                    invoice.payed_at,
                    invoice.check_number or "",
                    invoice.wire_transfer_number or "",
                ]
            )

        for i in range(2):
            csvwriter.writerow([] * len(invoice_headers))

        expense_headers = ["Dépense", "Date", "Montant"]
        expenses = (
            session.query(Expense)
            .filter(Expense.date >= self.start_date)
            .filter(Expense.date <= self.end_date)
        ).all()
        expense_total = sum([Decimal(expense.price) for expense in expenses]).quantize(
            Decimal("1.00")
        )

        for expense in expenses:
            csvwriter.writerow(expense_headers)
            csvwriter.writerow([expense.label, expense.date, expense.price])

        for i in range(2):
            csvwriter.writerow([] * len(expense_headers))
        csvwriter.writerow(["Total facturé", invoice_total])
        csvwriter.writerow(["Total dépensé", expense_total])
        csvwriter.writerow(["Total", str(invoice_total - expense_total)])

        csvfile.flush()
        csvfile.seek(0)
        return csvfile.read()
