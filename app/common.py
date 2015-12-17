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

def get_temperature(adc):
    # TODO add cell hardware version argument
    # on Xbee, 0x3FF (highest value on a 10-bit ADC) corresponds to 3.3V...ish:
    voltage = adc / 0x3FF * 3.3
    # on MCP9700A, 0.5V is 0°C, and every 0.01V difference is 1°C difference:
    celsius = (voltage - 0.5) / 0.01
    fahrenheit = celsius * (212 - 32) / 100 + 32
    return round(fahrenheit, 2)

def add_temperature(row):
    if not row['temperature']:
        row['temperature'] = get_temperature(row['adc'])
