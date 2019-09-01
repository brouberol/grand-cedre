import os
import logging

from flask import Flask

from .config import Config

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
template_dir = os.path.join(parent_dir, "templates")
static_dir = os.path.join(parent_dir, "static")


def setup_logging(app):
    app.logger.setLevel(logging.INFO)
    logging.getLogger("grand-cedre").setLevel(logging.DEBUG)
    logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)


def create_app():
    app = Flask("grand-cedre", template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(Config.from_env())
    setup_logging(app)
    return app


app = create_app()

import grand_cedre.web.admin
import grand_cedre.web.db
import grand_cedre.web.babel
import grand_cedre.web.cli
import grand_cedre.web.views
