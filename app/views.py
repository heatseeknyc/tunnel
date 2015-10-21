from datetime import datetime, timezone
import logging
import operator
import subprocess

import flask
import flask.views

from . import app, common


logging.basicConfig(level=logging.INFO)

LIVE_SLEEP_PERIOD = (59*60 + 50) * 100  # 59m50s in centiseconds

db = common.get_db()


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

def get_xbee_id(id, cursor):
    if len(id) == 16: return id  # already an xbee id
    cursor.execute('select id from xbees where short_id=%s', (id,))
    row = cursor.fetchone()
    if not row: flask.abort(404)
    return row['id']

def time_since(then):
    since = datetime.now(timezone.utc) - then
    if since.days: return '{} days ago'.format(since.days)
    if since.seconds >= 60 * 60: return '{} hours ago'.format(round(since.seconds / 60 / 60))
    if since.seconds >= 60: return '{} minutes ago'.format(round(since.seconds / 60))
    if since.seconds >= 2: return '{} seconds ago'.format(since.seconds)
    return 'just now'


@app.route('/')
def setup_index():
    return flask.render_template('setup/index.html')

@app.route('/<id>')
def setup_hub(id):
    if len(id) == 16:
        cursor = db.cursor()
        cursor.execute('select short_id from xbees where id=%s', (id,))
        row = cursor.fetchone()
        if row: return flask.redirect(flask.url_for('setup_hub', id=row['short_id']))

    return flask.render_template('setup/hub.html',
                                 hub_partial=setup_hub_partial(id),
                                 cells_partial=setup_hub_cells_partial(id))

@app.route('/<id>/_hub')
def setup_hub_partial(id):
    cursor = db.cursor()
    hub_id = get_xbee_id(id, cursor)
    cursor.execute('select sleep_period, time from hubs where hub_id=%s'
                   ' order by time desc limit 1', (hub_id,))
    hub = cursor.fetchone()
    cursor.execute('select sleep_period, time from temperatures where hub_id=%s'
                   ' order by time desc limit 1', (hub_id,))
    temperature = cursor.fetchone()

    # use the most recent of the sightings:
    if hub and temperature: hub = max(hub, temperature, key=operator.itemgetter('time'))
    else: hub = hub or temperature

    if hub:
        hub = dict(live=hub['sleep_period'] == LIVE_SLEEP_PERIOD,
                   since=time_since(hub['time']))
    return flask.render_template('setup/_hub.html', hub=hub)

@app.route('/<id>/_cells')
def setup_hub_cells_partial(id):
    cursor = db.cursor()
    # select most recent row for each cell of this hub, and join on short id:
    cursor.execute('select distinct on (cell_id) cell_id, short_id, time'
                   ' from temperatures left join xbees on xbees.id=cell_id where hub_id=%s'
                   ' order by cell_id, time desc', (get_xbee_id(id, cursor),))
    cells = [dict(id=c['short_id'] or c['cell_id'],
                  since=time_since(c['time']))
             for c in sorted(cursor.fetchall(), key=operator.itemgetter('time'), reverse=True)]

    return flask.render_template('setup/_cells.html', cells=cells)

@app.route('/<id>', methods=('PATCH',))
def setup_patch_hub(id):
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
def relay_old_hubs_post():
    return Hub.put(flask.request.form['hub'])

@app.route('/hubs/')
def relay_hubs():
    cursor = db.cursor()
    cursor.execute('select hub_id, max(time) as time from hubs'
                   ' group by hub_id order by time desc')
    return flask.render_template('relay/hubs.html', hubs=cursor.fetchall())

@route('/hubs/<id>', 'relay_hub')
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

@app.route('/cells/<id>')
def relay_cell(id):
    cursor = db.cursor()
    cursor.execute('select hub_id, max(time) as time from temperatures'
                   ' where cell_id=%s group by hub_id order by time desc', (id,))
    hubs = cursor.fetchall()
    cursor.execute('select hub_id, temperature, sleep_period, relay, hub_time, time, relayed_time'
                   ' from temperatures where cell_id=%s order by hub_time desc limit 100', (id,))
    temperatures = cursor.fetchall()
    return flask.render_template('relay/cell.html', hubs=hubs, temperatures=temperatures)

# old hub firmware doesn't use a trailing slash:
@app.route('/temperatures', methods=('POST',))
def relay_old_temperatures_post():
    return Temperatures.post()

@route('/temperatures/', 'relay_temperatures')
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
