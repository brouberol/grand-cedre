import tempfile
import os

from weasyprint import HTML
from flask import make_response, redirect, abort

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

    pdf = invoice.to_pdf(app.jinja_env)
    response = make_response(pdf)
    response.headers["Content-type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename={invoice.filename}"
    return response


@app.route("/balance/<int:balance_id>/csv")
def download_balance_sheet_as_csv(balance_id):
    balance_sheet = db.session.query(BalanceSheet).get(balance_id)
    if not balance_sheet:
        abort(404)

    csv = balance_sheet.to_csv(db.session)
    response = make_response(csv)
    response.headers["Content-type"] = "application/csv; charset=utf-8"
    response.headers[
        "Content-Disposition"
    ] = f"attachment; filename={balance_sheet.filename('csv')}"
    return response
