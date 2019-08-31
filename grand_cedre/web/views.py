import tempfile

from weasyprint import HTML
from flask import make_response, redirect, abort

from . import app
from .db import db
from grand_cedre.models.invoice import Invoice


@app.route("/")
def app_index():
    return redirect("/admin")


@app.route("/invoice/<int:invoice_id>/pdf")
def download_invoice_as_pdf(invoice_id):
    invoice = db.session.query(Invoice).get(invoice_id)
    if not invoice:
        abort(404)
    html = invoice.to_html()
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w") as tmphtml:
        tmphtml.write(html)
        tmphtml.flush()
        pdf = HTML(tmphtml.name).write_pdf()
    response = make_response(pdf)
    response.headers["Content-type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename={invoice.filename}"
    return response
