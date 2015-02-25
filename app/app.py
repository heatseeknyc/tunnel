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
        cursor.execute('select distinct on (hub_id) hub_id, time, port'
                       ' from hubs order by hub_id, time desc')
        hubs = sorted(cursor.fetchall(), key=operator.itemgetter('time'), reverse=True)
        return flask.render_template('hubs.html', hubs=hubs)

    def post(self):
        db.cursor().execute('insert into hubs (hub_id, port)'
                            ' values (%(hub)s, %(port)s)', flask.request.form)
        return 'ok'

@route('/hubs/<hub_id>', 'hub')
class Hub(flask.views.MethodView):
    def get(self, hub_id):
        cursor = db.cursor()
        cursor.execute('select distinct on (cell_id) hub_id, cell_id from readings'
                       ' where hub_id=%s order by cell_id', (hub_id,))
        cells = cursor.fetchall()
        cursor.execute('select time, port from hubs'
                       ' where hub_id=%s order by time desc', (hub_id,))
        logs = cursor.fetchall()
        return flask.render_template('hub.html', cells=cells, logs=logs)

@route('/readings', 'readings')
class Readings(flask.views.MethodView):
    def get(self):
        cursor = db.cursor()
        cursor.execute('select * from readings order by time desc limit 100')
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
