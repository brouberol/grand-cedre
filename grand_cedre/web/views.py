import tempfile
import os
import csv

from weasyprint import HTML
from flask import make_response, redirect, abort
from decimal import Decimal

from . import app
from .db import db
from grand_cedre.models.invoice import Invoice
from grand_cedre.models.balance import BalanceSheet

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
output_dir = os.path.join(parent_dir, "output")


@app.route("/")
def app_index():
    return redirect("/admin")


@app.route("/invoice/<int:invoice_id>/pdf")
def download_invoice_as_pdf(invoice_id):
    invoice = db.session.query(Invoice).get(invoice_id)
    if not invoice:
        abort(404)
    html = invoice.to_html(app.jinja_env)
    with tempfile.NamedTemporaryFile(
        dir=output_dir, suffix=".html", mode="w"
    ) as tmphtml:
        tmphtml.write(html)
        tmphtml.flush()
        pdf = HTML(tmphtml.name).write_pdf()
    response = make_response(pdf)
    response.headers["Content-type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename={invoice.filename}"
    return response


@app.route("/balance/<int:balance_id>/csv")
def download_balance_sheet_as_csv(balance_id):
    balance_sheet = db.session.query(BalanceSheet).get(balance_id)
    if not balance_sheet:
        abort(404)
    invoices = (
        db.session.query(Invoice)
        .filter(Invoice.payed_at.isnot(None))
        .filter(Invoice.payed_at >= balance_sheet.start_date)
        .filter(Invoice.payed_at <= balance_sheet.end_date)
    ).all()
    total = str(sum([invoice.total_price for invoice in invoices]))
    with tempfile.NamedTemporaryFile(
        suffix=".csv", mode="w", delete=False, encoding="utf-8"
    ) as tmpcsv:
        csvwriter = csv.writer(tmpcsv)
        headers = [
            "# Facture",
            "Client",
            "Période",
            "Total",
            "Date d'encaissement",
            "# Chèque",
            "# Virement",
        ]
        for invoice in invoices:
            csvwriter.writerow(headers)
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
        csvwriter.writerow([] * len(headers))
        csvwriter.writerow(["Total", total])

    with open(tmpcsv.name, "r") as tmpcsv:
        response = make_response(tmpcsv.read())

    os.unlink(tmpcsv.name)
    response.headers["Content-type"] = "application/csv; charset=utf-8"
    response.headers[
        "Content-Disposition"
    ] = f"attachment; filename={balance_sheet.filename('csv')}"
    return response
