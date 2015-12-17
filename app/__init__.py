import logging

import flask

from . import common


logging.basicConfig(level=logging.INFO)

app = flask.Flask(__name__)
db = common.get_db()

@app.teardown_request
def teardown_request(exception):
    if exception:
        db.rollback()
        logging.error(exception)
    else:
        db.commit()


from .views import setup
from .views import relay
