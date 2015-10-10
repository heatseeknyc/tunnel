from datetime import datetime
import logging
import operator
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


def get_xbee_id(short_id, cursor):
    cursor.execute('select id from xbees where short_id=%s', (short_id,))
    row = cursor.fetchone()
    if row: return row['id']


def time_since(then):
    since = datetime.now() - then
    if since.days: return '{} days ago'.format(since.days)
    if since.seconds >= 60 * 60: return '{} hours ago'.format(round(since.seconds / 60 / 60))
    if since.seconds >= 60: return '{} minutes ago'.format(round(since.seconds / 60))
    if since.seconds >= 2: return '{} seconds ago'.format(since.seconds)
    return 'just now'


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

        if len(id) == 16:
            cursor.execute('select short_id from xbees where id=%s', (id,))
            row = cursor.fetchone()
            if row: return flask.redirect(flask.url_for('setup-hub', id=row['short_id']))
            hub_id = id
        else:
            hub_id = get_xbee_id(id, cursor)
            if not hub_id: return 'no such id', 404

        cursor.execute('select sleep_period, time from hubs where hub_id=%s'
                       ' order by time desc limit 1', (hub_id,))
        hub = cursor.fetchone()
        # select most recent row for each cell of this hub, and join on short id:
        cursor.execute('select distinct on (cell_id) cell_id, short_id, time'
                       ' from temperatures left join xbees on xbees.id=cell_id where hub_id=%s'
                       ' order by cell_id, time desc', (hub_id,))
        cells = sorted(cursor.fetchall(), key=operator.itemgetter('time'), reverse=True)

        if hub:
            # seeing a cell counts as seeing the hub:
            time = max(hub['time'], cells[0]['time']) if cells else hub['time']
            hub = dict(live=hub['sleep_period'] == LIVE_SLEEP_PERIOD,
                       since=time_since(time))
        cells = [dict(id=c['short_id'] or c['cell_id'],
                      since=time_since(c['time']))
                 for c in cells]

        return flask.render_template('setup/hub.html', hub=hub, cells=cells)

    @staticmethod
    def patch(id):
        cursor = db.cursor()

        hub_id = get_xbee_id(id, cursor)
        if not hub_id: return 'no such id', 404

        # TODO actually look at the data, which should be something like hourly=true...
        cursor.execute('select port from hubs where hub_id=%s and port is not null'
                       ' order by time desc limit 1', (hub_id,))
        row = cursor.fetchone()
        if not row: return 'no ssh port for hub', 404

        logging.info(subprocess.check_output([
            'ssh', '-p', str(row['port']), 'localhost',
            'sudo PYTHONPATH=firmware python3 -m hub.set_sleep_period {}'.format(LIVE_SLEEP_PERIOD)
        ]))
        return 'ok'


# convert old hub firmware's POSTs to /hubs to PUTs to /hubs/<id>:
@app.route('/hubs', methods=('POST',))
def old_hubs_post():
    return Hub.put(flask.request.form['hub'])

@route('/hubs/', 'relay-hubs')
class Hubs(flask.views.MethodView):
    @staticmethod
    def get():
        cursor = db.cursor()
        cursor.execute('select hub_id, max(time) as time from hubs'
                       ' group by hub_id order by time desc')
        return flask.render_template('relay/hubs.html', hubs=cursor.fetchall())


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

    @staticmethod
    def put(id):
        hub = flask.request.form.copy()
        hub['id'] = id
        if not hub.get('port'): hub['port'] = None  # missing or empty => null
        db.cursor().execute('insert into hubs (hub_id, pi_id, sleep_period, port)'
                            ' values (%(id)s, %(pi)s, %(sp)s, %(port)s)', hub)
        return 'ok'


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


# old hub firmware doesn't use a trailing slash:
@app.route('/temperatures', methods=('POST',))
def old_temperatures_post():
    return Temperatures.post()

@route('/temperatures/', 'relay-temperatures')
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
