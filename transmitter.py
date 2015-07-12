"""Continually transmit readings from database to heatseeknyc.com."""

import logging
import time

import psycopg2
import psycopg2.extras
import requests


logging.basicConfig(level=logging.INFO)


def transmit_reading(reading):
    """Transmit a single reading to heatseeknyc.com."""
    reading = dict(sensor_name=reading['cell_id'],
                   temp=reading['temperature'],
                   time=reading['hub_time'].timestamp(),
                   verification='c0ffee')
    logging.info('POSTing {}...'.format(reading))
    response = requests.post('http://heatseeknyc.com/readings.json', json=dict(reading=reading))
    if response.status_code == 200:
        return True
    else:
        logging.error('request %s got %s response %s',
                      response.request.body, response.status_code, response.text)
        return False


def transmit():
    """Continually transmit readings from database to heatseeknyc.com."""
    database = psycopg2.connect(host='localhost', user='webdb', password='password',
                                cursor_factory=psycopg2.extras.DictCursor)
    while True:
        with database:
            cursor = database.cursor()
            cursor.execute('select * from readings'
                           ' where relay and relayed_time is null')
            readings = cursor.fetchall()
        if readings: logging.info('%s unrelayed readings', len(readings))

        failed_cell_ids = set()
        for reading in readings:
            cell_id = reading['cell_id']
            if cell_id not in failed_cell_ids:
                if transmit_reading(reading):
                    with database:
                        database.cursor().execute('update readings set relayed_time = now()'
                                                  ' where id=%(id)s', reading)
                else:
                    failed_cell_ids.add(cell_id)
                time.sleep(1)

        time.sleep(1)

def main():
    while True:
        try:
            transmit()
        except Exception:
            logging.exception('error, retrying...')
            time.sleep(1)

if __name__ == '__main__':
    main()
