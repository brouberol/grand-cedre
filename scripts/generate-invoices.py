import os
import sys

current_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, parent_dir)

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from grand_cedre.invoice import generate_invoice_per_user


engine = create_engine(os.environ["SQLALCHEMY_DATABASE_URI"])
Session = sessionmaker(bind=engine)


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("grand-cedre-billing")
    logger.setLevel(logging.INFO)
    logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)
    return logger


def main():
    setup_logging()
    session = Session()
    generate_invoice_per_user(session)
    session.commit()
    session.close()


if __name__ == "__main__":
    main()
