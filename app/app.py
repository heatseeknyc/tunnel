from datetime import datetime
import logging; logging.basicConfig(level=logging.INFO)
import operator

import flask
import flask.views
import psycopg2
import psycopg2.extras


app = flask.Flask(__name__)
db = psycopg2.connect(host='localhost', user='webdb', password='password',
                      cursor_factory=psycopg2.extras.DictCursor)

@app.teardown_request
def teardown_request(exception):
    logging.info('sup')
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
    def get(self):
        return 'Hello, cruel world!'


@route('/hubs', 'hubs')
class Hubs(flask.views.MethodView):
    def get(self):
        cursor = db.cursor()
        cursor.execute('select hub_id, max(time) as time from hubs'
                       ' group by hub_id order by time desc')
        return flask.render_template('hubs.html', hubs=cursor.fetchall())

    def post(self):
        db.cursor().execute('insert into hubs (hub_id, port)'
                            ' values (%(hub)s, %(port)s)', flask.request.form)
        return 'ok'

@route('/hubs/<hub_id>', 'hub')
class Hub(flask.views.MethodView):
    def get(self, hub_id):
        cursor = db.cursor()
        cursor.execute('select time, port from hubs'
                       ' where hub_id=%s order by time desc', (hub_id,))
        logs = cursor.fetchall()
        cursor.execute('select cell_id, max(time) as time from readings'
                       ' where hub_id=%s group by cell_id order by time desc', (hub_id,))
        cells = cursor.fetchall()
        cursor.execute('select hub_time, cell_id, temperature, relay, relayed_time from readings'
                       ' where hub_id=%s order by hub_time desc limit 1000', (hub_id,))
        readings = cursor.fetchall()
        return flask.render_template('hub.html', logs=logs, cells=cells, readings=readings)

@route('/readings', 'readings')
class Readings(flask.views.MethodView):
    def get(self):
        cursor = db.cursor()
        cursor.execute('select hub_time, hub_id, cell_id, temperature, relay, relayed_time'
                       ' from readings order by hub_time desc limit 1000')
        return flask.render_template('readings.html', readings=cursor.fetchall())

    def post(self):
        d = flask.request.form.copy()
        d['time'] = datetime.fromtimestamp(int(d['time']))
        d['relay'] = True # TODO this should correspond to whether hub is in live mode
        db.cursor().execute('insert into readings (hub_id, hub_time, cell_id, temperature, relay)'
                            ' values (%(hub)s, %(time)s, %(cell)s, %(temp)s, %(relay)s)', d)
        return 'ok'


if __name__ == '__main__':
    app.run(debug=True)
