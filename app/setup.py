from datetime import datetime, timezone
import operator

import flask

from . import app, common, db


def time_since(then):
    since = datetime.now(timezone.utc) - then
    if since.days: return '{} days ago'.format(since.days)
    if since.seconds >= 60 * 60: return '{} hours ago'.format(round(since.seconds / 60 / 60))
    if since.seconds >= 60: return '{} minutes ago'.format(round(since.seconds / 60))
    if since.seconds >= 2: return '{} seconds ago'.format(since.seconds)
    return 'just now'


@app.route('/')
def index():
    return flask.render_template('setup/index.html')

@app.route('/<id>')
def setup_hub(id):
    cursor = db.cursor()

    if len(id) == 16:
        cursor.execute('select short_id from xbees where id=%s', (id,))
        row = cursor.fetchone()
        if row: return flask.redirect(flask.url_for('setup_hub', id=row['short_id']))

    return flask.render_template('setup/hub.html',
                                 hub_id=common.get_xbee_id(id, cursor),
                                 hub_partial=setup_hub_partial(id),
                                 cells_partial=setup_cells_partial(id))

@app.route('/<id>/_hub')
def setup_hub_partial(id):
    cursor = db.cursor()
    hub_id = common.get_xbee_id(id, cursor)
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
        hub = dict(live=hub['sleep_period'] == common.LIVE_SLEEP_PERIOD,
                   since=time_since(hub['time']))
    return flask.render_template('setup/_hub.html', hub=hub)

@app.route('/<id>/_cells')
def setup_cells_partial(id):
    cursor = db.cursor()
    # select most recent row for each cell of this hub, and join on short id:
    cursor.execute('select distinct on (cell_id) cell_id, short_id, time'
                   ' from temperatures left join xbees on xbees.id=cell_id where hub_id=%s'
                   ' order by cell_id, time desc', (common.get_xbee_id(id, cursor),))
    cells = [dict(id=c['short_id'] or c['cell_id'],
                  since=time_since(c['time']))
             for c in sorted(cursor.fetchall(), key=operator.itemgetter('time'), reverse=True)]

    return flask.render_template('setup/_cells.html', cells=cells)
