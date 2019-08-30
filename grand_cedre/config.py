import os


def getenv(var):
    return os.environ[var]


class Config(object):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///data/data.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_ADMIN_SWATCH = "flatly"
    SECRET_KEY = b"\ry\xe0\x97\xe88\xed\x84\x05\xfdfN\x1daQ\xf8\x83!\xeanp\x80R\xd1"

    @classmethod
    def from_env(cls):
        env = os.getenv("APP_ENV", "dev")
        return {
            "dev": DevelopmentConfig,
            "prod": ProductionConfig,
            "test": TestingConfig,
        }[env]()


class ProductionConfig(Config):
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return os.environ["SQLALCHEMY_DATABASE_URI"]

    @property
    def SECRET_KEY(self):
        return os.environ["SECRET_KEY"]


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
