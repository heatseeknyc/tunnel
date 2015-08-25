from datetime import datetime
import logging
import subprocess

import flask
import flask.views
import psycopg2
import psycopg2.extras


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
        cursor.execute('select hub_id, max(time) as time from hubs'
                       ' group by hub_id order by time desc')
        return flask.render_template('hubs.html', hubs=cursor.fetchall())

    @staticmethod
    def post():
        db.cursor().execute('insert into hubs (hub_id, pi_id, port)'
                            ' values (%(hub)s, %(pi)s, %(port)s)', flask.request.form)
        return 'ok'


@route('/hubs/<id>', 'hub')
class Hub(flask.views.MethodView):
    @staticmethod
    def get(id):
        cursor = db.cursor()
        cursor.execute('select pi_id, port, time from hubs'
                       ' where hub_id=%s order by time desc limit 10', (id,))
        logs = cursor.fetchall()
        cursor.execute('select cell_id, max(time) as time from temperatures'
                       ' where hub_id=%s group by cell_id order by time desc', (id,))
        cells = cursor.fetchall()
        cursor.execute('select cell_id, temperature, relay, hub_time, relayed_time from temperatures'
                       ' where hub_id=%s order by hub_time desc limit 100', (id,))
        temperatures = cursor.fetchall()
        return flask.render_template('hub.html', logs=logs, cells=cells, temperatures=temperatures)

    @staticmethod
    def patch(id):
        # TODO actually look at the data, which should be something like hourly=true...
        cursor = db.cursor()
        cursor.execute('select port from hubs where hub_id=%s and port is not null'
                       ' order by time desc limit 1', (id,))
        row = cursor.fetchone()
        if not row: return 'no ssh port for hub', 404

        logging.info(subprocess.check_output(['ssh', '-p', str(row['port']), 'localhost',
                                              'cd firmware && sudo python3 -m hub.hourly']))
        return 'ok'


@route('/cells/<id>', 'cell')
class Cell(flask.views.MethodView):
    @staticmethod
    def get(id):
        cursor = db.cursor()
        cursor.execute('select hub_id, max(time) as time from temperatures'
                       ' where cell_id=%s group by hub_id order by time desc', (id,))
        hubs = cursor.fetchall()
        cursor.execute('select hub_id, temperature, relay, hub_time, relayed_time from temperatures'
                       ' where cell_id=%s order by hub_time desc limit 100', (id,))
        temperatures = cursor.fetchall()
        return flask.render_template('cell.html', hubs=hubs, temperatures=temperatures)


@route('/temperatures', 'temperatures')
class Temperatures(flask.views.MethodView):
    @staticmethod
    def get():
        cursor = db.cursor()
        cursor.execute('select hub_id, cell_id, temperature, relay, hub_time, relayed_time'
                       ' from temperatures order by hub_time desc limit 100')
        return flask.render_template('temperatures.html', temperatures=cursor.fetchall())

    @staticmethod
    def post():
        d = flask.request.form.copy()
        d['time'] = datetime.fromtimestamp(int(d['time']))
        d['relay'] = True  # TODO this should correspond to whether hub is in live mode
        cursor = db.cursor()

        cursor.execute('select count(*) from temperatures where'
                       ' cell_id=%(cell)s and temperature=%(temp)s and hub_time=%(time)s', d)
        count, = cursor.fetchone()
        if count:  # duplicate reading, store but don't relay
            d['relay'] = False  # TODO fix hub transmitter instead

        cursor.execute('insert into temperatures (hub_id, cell_id, temperature, relay, hub_time)'
                       ' values (%(hub)s, %(cell)s, %(temp)s, %(relay)s, %(time)s)', d)
        return 'ok'


if __name__ == '__main__':
    app.run(debug=True)
