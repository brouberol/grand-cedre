from flask_babelex import Babel

from . import app

babel = Babel(app)


@babel.localeselector
def get_locale():
    return "fr"
