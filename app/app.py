from datetime import datetime
import logging
import subprocess

import flask
import flask.views
import psycopg2
import psycopg2.extras


LIVE_SLEEP_PERIOD = (59*60 + 50) * 100  # 59m50s in centiseconds


logging.basicConfig(level=logging.INFO)


app = flask.Flask(__name__)
db = psycopg2.connect(host='localhost', user='webdb', password='password',
                      cursor_factory=psycopg2.extras.DictCursor)


@app.teardown_request
def teardown_request(exception):
    if exception:
        db.rollback()
        logging.error(exception)
    else:
        db.commit()


def route(path, name):
    """decorator to add a route to a View class"""
    def f(cls):
        app.add_url_rule(path, view_func=cls.as_view(name))
        return cls
    return f


@route('/', 'setup-index')
class Index(flask.views.MethodView):
    @staticmethod
    def get():
        return flask.render_template('setup/index.html')


@route('/<id>', 'setup-hub')
class Hub(flask.views.MethodView):
    @staticmethod
    def get(id):
        cursor = db.cursor()
        cursor.execute('select pi_id, sleep_period, port, time from hubs'
                       ' where hub_id=%s order by time desc limit 10', (id,))
        logs = cursor.fetchall()
        cursor.execute('select cell_id, max(time) as time from temperatures'
                       ' where hub_id=%s group by cell_id order by time desc', (id,))
        cells = cursor.fetchall()
        return flask.render_template('setup/hub.html', logs=logs, cells=cells)

    @staticmethod
    def patch(id):
        # TODO actually look at the data, which should be something like hourly=true...
        cursor = db.cursor()
        cursor.execute('select port from hubs where hub_id=%s and port is not null'
                       ' order by time desc limit 1', (id,))
        row = cursor.fetchone()
        if not row: return 'no ssh port for hub', 404

        logging.info(subprocess.check_output([
            'ssh', '-p', str(row['port']), 'localhost',
            'sudo PYTHONPATH=firmware python3 -m hub.set_sleep_period {}'.format(LIVE_SLEEP_PERIOD)
        ]))
        return 'ok'


@route('/hubs', 'relay-hubs')
class Hubs(flask.views.MethodView):
    @staticmethod
    def get():
        cursor = db.cursor()
        cursor.execute('select hub_id, max(time) as time from hubs'
                       ' group by hub_id order by time desc')
        return flask.render_template('relay/hubs.html', hubs=cursor.fetchall())

    @staticmethod
    def post():
        d = flask.request.form.copy()
        if not d.get('port'): d['port'] = None  # missing or empty => null
        db.cursor().execute('insert into hubs (hub_id, pi_id, sleep_period, port)'
                            ' values (%(hub)s, %(pi)s, %(sp)s, %(port)s)', d)
        return 'ok'


@route('/hubs/<id>', 'relay-hub')
class Hub(flask.views.MethodView):
    @staticmethod
    def get(id):
        cursor = db.cursor()
        cursor.execute('select pi_id, sleep_period, port, time from hubs'
                       ' where hub_id=%s order by time desc limit 10', (id,))
        logs = cursor.fetchall()
        cursor.execute('select cell_id, max(time) as time from temperatures'
                       ' where hub_id=%s group by cell_id order by time desc', (id,))
        cells = cursor.fetchall()
        cursor.execute('select cell_id, temperature, sleep_period, relay, hub_time, time, relayed_time from temperatures'
                       ' where hub_id=%s order by hub_time desc limit 100', (id,))
        temperatures = cursor.fetchall()
        return flask.render_template('relay/hub.html', logs=logs, cells=cells, temperatures=temperatures)


@route('/cells/<id>', 'relay-cell')
class Cell(flask.views.MethodView):
    @staticmethod
    def get(id):
        cursor = db.cursor()
        cursor.execute('select hub_id, max(time) as time from temperatures'
                       ' where cell_id=%s group by hub_id order by time desc', (id,))
        hubs = cursor.fetchall()
        cursor.execute('select hub_id, temperature, sleep_period, relay, hub_time, time, relayed_time from temperatures'
                       ' where cell_id=%s order by hub_time desc limit 100', (id,))
        temperatures = cursor.fetchall()
        return flask.render_template('relay/cell.html', hubs=hubs, temperatures=temperatures)


@route('/temperatures', 'relay-temperatures')
class Temperatures(flask.views.MethodView):
    @staticmethod
    def get():
        cursor = db.cursor()
        cursor.execute('select hub_id, cell_id, temperature, sleep_period, relay, hub_time, time, relayed_time'
                       ' from temperatures order by hub_time desc limit 100')
        return flask.render_template('relay/temperatures.html', temperatures=cursor.fetchall())

    @staticmethod
    def post():
        d = flask.request.form.copy()
        d['time'] = datetime.fromtimestamp(int(d['time']))
        d['relay'] = int(d['sp']) == LIVE_SLEEP_PERIOD
        db.cursor().execute('insert into temperatures (hub_id, cell_id, temperature, sleep_period, relay, hub_time)'
                            ' values (%(hub)s, %(cell)s, %(temp)s, %(sp)s, %(relay)s, %(time)s)', d)
        return 'ok'


if __name__ == '__main__':
    app.run(debug=True)
