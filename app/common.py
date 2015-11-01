import os

import flask
import psycopg2
import psycopg2.extras


LIVE_SLEEP_PERIOD = (59*60 + 50) * 100  # 59m50s in centiseconds


def get_db():
    return psycopg2.connect(host=os.environ['DB_PORT_5432_TCP_ADDR'],
                            port=os.environ['DB_PORT_5432_TCP_PORT'],
                            user='postgres',
                            cursor_factory=psycopg2.extras.DictCursor)

def get_xbee_id(id, cursor):
    if len(id) == 16: return id  # already an xbee id
    cursor.execute('select id from xbees where short_id=%s', (id,))
    row = cursor.fetchone()
    if not row: flask.abort(404)
    return row['id']
