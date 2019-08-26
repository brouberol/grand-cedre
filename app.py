from flask import Flask
from flask_admin import Admin
from flask_sqlalchemy import SQLAlchemy
from flask_admin.contrib.sqla import ModelView

from grand_cedre.models.client import Client
from grand_cedre.models.contract import Contract


app = Flask("grand-cedre")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data/data.db"
app.config["FLASK_ADMIN_SWATCH"] = "flatly"
db = SQLAlchemy(app)
admin = Admin(app, name="grand-cedre", template_mode="bootstrap3")

admin.add_view(ModelView(Client, db.session))
admin.add_view(ModelView(Contract, db.session))
