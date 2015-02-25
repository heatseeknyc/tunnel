import logging; logging.basicConfig(level=logging.INFO)
import time

import psycopg2
import psycopg2.extras
import requests


def transmit_reading(r):
    reading = dict(sensor_name=r['cell_id'],
                   temp=r['temperature'],
                   time=r['hub_time'].timestamp(),
                   verification='c0ffee')
    response = requests.post('http://heatseeknyc.com/readings.json',
                             json=dict(reading=reading))
    if response.status_code == 200: return True
    else:
        logging.error('request {} got {} response {}'.format(response.request.body, response.status_code, response.text))
        return False

def transmit():
    db = psycopg2.connect(host='localhost', user='webdb', password='password',

                          cursor_factory=psycopg2.extras.DictCursor)
    while True:
        with db:
            cursor = db.cursor()
            cursor.execute('select * from readings'
                           ' where relay and relayed_time is null')
            readings = cursor.fetchall()
        if readings: logging.info('{} unrelayed readings'.format(len(readings)))

        failed_cell_ids = set()
        for reading in readings:
            cell_id = reading['cell_id']
            if cell_id not in failed_cell_ids:
                if transmit_reading(reading):
                    with db:
                        db.cursor().execute('update readings set relayed_time = now()'
                                            ' where id=%(id)s', reading)
                else: failed_cell_ids.add(cell_id)
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
