"""Continually transmit temperatures from database to heatseeknyc.com."""

import logging
import time

import psycopg2
import psycopg2.extras
import requests


logging.basicConfig(level=logging.INFO)


def transmit_temperature(temperature):
    """Transmit a single temperature to heatseeknyc.com."""
    reading = dict(sensor_name=temperature['cell_id'],
                   temp=temperature['temperature'],
                   time=temperature['hub_time'].timestamp(),
                   verification='c0ffee')
    logging.info('POSTing {}...'.format(reading))
    response = requests.post('http://heatseeknyc.com/readings.json',
                             json=dict(reading=reading))
    if response.status_code == 200:
        return True
    else:
        logging.error('request %s got %s response %s',
                      response.request.body, response.status_code, response.text)
        return False


def transmit():
    """Continually transmit temperatures from database to heatseeknyc.com."""
    database = psycopg2.connect(host='localhost', user='webdb', password='password',
                                cursor_factory=psycopg2.extras.DictCursor)
    while True:
        with database:
            cursor = database.cursor()
            cursor.execute('select * from temperatures'
                           ' where relay and relayed_time is null')
            temperatures = cursor.fetchall()
        if temperatures: logging.info('%s unrelayed temperatures', len(temperatures))

        failed_cell_ids = set()
        for temperature in temperatures:
            cell_id = temperature['cell_id']
            if cell_id not in failed_cell_ids:
                if transmit_temperature(temperature):
                    with database:
                        database.cursor().execute('update temperatures set relayed_time = now()'
                                                  ' where id=%(id)s', temperature)
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
