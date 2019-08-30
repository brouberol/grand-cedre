import tempfile
import os

from weasyprint import HTML
from flask import Flask, abort, make_response, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_babelex import Babel

from grand_cedre.models.booking import Booking
from grand_cedre.models.invoice import Invoice
from grand_cedre.config import Config

current_dir = os.path.abspath(os.path.dirname(__file__))
output_dir = os.path.join(current_dir, "grand_cedre", "output")
template_dir = os.path.join(current_dir, "grand_cedre", "templates")
static_dir = os.path.join(current_dir, "grand_cedre", "static")

app = Flask("grand-cedre", template_folder=template_dir, static_folder=static_dir)
app.config.from_object(Config.from_env())
db = SQLAlchemy(app)
babel = Babel(app)


@babel.localeselector
def get_locale():
    return "fr"


@app.route("/")
def app_index():
    return redirect("/admin")


@app.route("/invoice/<int:invoice_id>/pdf")
def download_invoice_as_pdf(invoice_id):
    invoice = db.session.query(Invoice).get(invoice_id)
    if not invoice:
        abort(404)
    html = invoice.to_html()
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
