from datetime import datetime
import logging; logging.basicConfig(level=logging.INFO)
import operator
import subprocess

import flask
import flask.views
import psycopg2
import psycopg2.extras


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


@route('/', 'index')
class Index(flask.views.MethodView):
    @staticmethod
    def get():
        return flask.render_template('index.html')


@route('/hubs', 'hubs')
class Hubs(flask.views.MethodView):
    @staticmethod
    def get():
        cursor = db.cursor()
        cursor.execute('select id, xbee_id, port, time from hubs'
                       ' order by time desc')
        return flask.render_template('hubs.html', hubs=cursor.fetchall())

    @staticmethod
    def post():
        with db:
            db.cursor().execute('insert into hubs_log (hub_id, xbee_id, port)'
                                ' values (%(hub)s, %(xbee)s, %(port)s)', flask.request.form)

        # psotgres can't upsert, so we try to insert, and if not then update:
        try:
            with db:
                db.cursor().execute('insert into hubs (id, xbee_id, port)'
                                    ' values (%(hub)s, %(xbee)s, %(port)s)', flask.request.form)
        except psycopg2.IntegrityError:
            updates = {'time': 'now()'}
            if flask.request.form.get('xbee'): updates['xbee_id'] = '%(xbee)s'
            if flask.request.form.get('port'): updates['port'] = '%(port)s'
            updates = ', '.join('{}={}'.format(k, v) for k, v in updates.items())
            db.cursor().execute('update hubs set {} where id=%(hub)s'.format(updates),
                                flask.request.form)

        return 'ok'


@route('/hubs/<xbee_id>', 'hub')
class Hub(flask.views.MethodView):
    @staticmethod
    def get(xbee_id):
        hub_id = get_hub_id(xbee_id)
        if not hub_id: flask.abort(404)

        cursor = db.cursor()

        cursor.execute('select time, port from hubs_log'
                       ' where hub_id=%s order by time desc limit 10', (hub_id,))
        logs = cursor.fetchall()

        cursor.execute('select cell_id, max(time) as time from readings'
                       ' where hub_id=%s group by cell_id order by time desc', (hub_id,))
        cells = cursor.fetchall()

        cursor.execute('select hub_time, cell_id, temperature, relay, relayed_time from readings'
                       ' where hub_id=%s order by hub_time desc limit 1000', (hub_id,))
        readings = cursor.fetchall()

        return flask.render_template('hub.html', logs=logs, cells=cells, readings=readings)

    @staticmethod
    def patch(xbee_id):
        hub_id = get_hub_id(xbee_id)
        if not hub_id: flask.abort(404)

        # TODO actually look at the data, which should be something like hourly=true...
        cursor = db.cursor()
        cursor.execute('select port from hubs where id=%s and port is not null', (hub_id,))
        row = cursor.fetchone()
        if not row: return 'no ssh port for hub', 404

        logging.info(subprocess.check_output(['ssh', '-p', str(row['port']), 'localhost',
                                              'cd firmware && sudo python3 -m hub.hourly']))
        return 'ok'


@route('/cells/<cell_id>', 'cell')
class Cell(flask.views.MethodView):
    @staticmethod
    def get(cell_id):
        cursor = db.cursor()
        cursor.execute('select hub_id, max(time) as time from readings'
                       ' where cell_id=%s group by hub_id order by time desc', (cell_id,))
        hubs = cursor.fetchall()
        cursor.execute('select hub_time, hub_id, temperature, relay, relayed_time from readings'
                       ' where cell_id=%s order by hub_time desc limit 1000', (cell_id,))
        readings = cursor.fetchall()
        return flask.render_template('cell.html', hubs=hubs, readings=readings)


@route('/readings', 'readings')
class Readings(flask.views.MethodView):
    @staticmethod
    def get():
        cursor = db.cursor()
        cursor.execute('select hub_time, hub_id, cell_id, temperature, relay, relayed_time'
                       ' from readings order by hub_time desc limit 1000')
        return flask.render_template('readings.html', readings=cursor.fetchall())

    @staticmethod
    def post():
        d = flask.request.form.copy()
        d['time'] = datetime.fromtimestamp(int(d['time']))
        d['relay'] = True  # TODO this should correspond to whether hub is in live mode
        cursor = db.cursor()

        cursor.execute('select count(*) from readings where'
                       ' cell_id=%(cell)s and hub_time=%(time)s and temperature=%(temp)s', d)
        count, = cursor.fetchone()
        if count:  # duplicate reading, store but don't relay
            d['relay'] = False

        cursor.execute('insert into readings (hub_id, hub_time, cell_id, temperature, relay)'
                       ' values (%(hub)s, %(time)s, %(cell)s, %(temp)s, %(relay)s)', d)
        return 'ok'


def get_hub_id(xbee_id):
    cursor = db.cursor()
    cursor.execute('select id from hubs where xbee_id=%s', (xbee_id,))
    row = cursor.fetchone()
    if row: return row['id']


if __name__ == '__main__':
    app.run(debug=True)
