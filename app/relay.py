from datetime import datetime
import logging
import operator
import os

import flask
import flask.views
import requests

from . import app, common, db


def route(path, name):
    """decorator to add a route to a View class"""
    def f(cls):
        app.add_url_rule(path, view_func=cls.as_view(name))
        return cls
    return f

@app.route('/hubs/')
def hubs():
    cursor = db.cursor()
    # select most recent row for each hub, and join on short id:
    cursor.execute('select distinct on (hub_id)'
                   ' hub_id, short_id, sleep_period, disk_free, uptime, version, port, time'
                   ' from hubs left join xbees on xbees.id=hub_id'
                   ' order by hub_id, time desc')
    hubs = sorted(cursor.fetchall(), key=operator.itemgetter('time'), reverse=True)
    return flask.render_template('relay/hubs.html', hubs=hubs)

@route('/hubs/<id>', 'hub')
class Hub(flask.views.MethodView):
    @staticmethod
    def get(id):
        cursor = db.cursor()

        if len(id) != 16:
            return flask.redirect(flask.url_for('hub', id=common.get_xbee_id(id, cursor)))

        cursor.execute('select pi_id, sleep_period, disk_free, uptime, version, port, time from hubs'
                       ' where hub_id=%s order by time desc limit 10', (id,))
        logs = cursor.fetchall()
        cursor.execute('select cell_id, max(time) as time from temperatures'
                       ' where hub_id=%s group by cell_id order by time desc', (id,))
        cells = cursor.fetchall()
        cursor.execute('select cell_id, temperature, sleep_period, relay, hub_time, time, relayed_time from temperatures'
                       ' where hub_id=%s order by hub_time desc limit 100', (id,))
        temperatures = cursor.fetchall()
        return flask.render_template('relay/hub.html', hubs=logs, cells=cells, temperatures=temperatures)

    @staticmethod
    def put(id):
        hub = flask.request.form.copy()
        hub['id'] = id
        for k in ('free', 'up', 'v', 'port'):  # optional parameters
            if not hub.get(k): hub[k] = None  # missing or empty => null
        db.cursor().execute('insert into hubs'
                            ' (hub_id, pi_id, sleep_period, disk_free, uptime, version, port)'
                            ' values (%(id)s, %(pi)s, %(sp)s, %(free)s, %(up)s, %(v)s, %(port)s)',
                            hub)
        return 'ok'

    @staticmethod
    def patch(id):
        cursor = db.cursor()
        # TODO actually look at the data, which should be something like hourly=true...
        cursor.execute('select port from hubs where hub_id=%s and port is not null'
                       ' order by time desc limit 1', (id,))
        row = cursor.fetchone()
        if not row: return 'no ssh port for hub', 404

        command = ('sudo PYTHONPATH=firmware python3 -m hub.set_sleep_period {}'
                   .format(common.LIVE_SLEEP_PERIOD))
        response = requests.post('http://{}:{}/{}'.format(os.environ['TUNNEL_PORT_80_TCP_ADDR'],
                                                          os.environ['TUNNEL_PORT_80_TCP_PORT'],
                                                          row['port']),
                                 dict(command=command))
        logging.info('tunnel response:\n' + response.text)
        response.raise_for_status()
        return 'ok'

# PATCHing doesn't play well with Chrome Data Compression Proxy, so we fake it with POST:
@app.route('/hubs/<id>/patch', methods=('POST',))
def hub_patch(id):
    return Hub.patch(id)


@app.route('/cells/<id>')
def cell(id):
    cursor = db.cursor()

    if len(id) != 16:
        return flask.redirect(flask.url_for('cell', id=common.get_xbee_id(id, cursor)))

    cursor.execute('select hub_id, max(time) as time from temperatures'
                   ' where cell_id=%s group by hub_id order by time desc', (id,))
    hubs = cursor.fetchall()
    cursor.execute('select hub_id, temperature, sleep_period, relay, hub_time, time, relayed_time'
                   ' from temperatures where cell_id=%s order by hub_time desc limit 100', (id,))
    temperatures = cursor.fetchall()
    return flask.render_template('relay/cell.html', hubs=hubs, temperatures=temperatures)

@route('/temperatures/', 'temperatures')
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
        d['relay'] = int(d['sp']) == common.LIVE_SLEEP_PERIOD
        db.cursor().execute('insert into temperatures (hub_id, cell_id, temperature, sleep_period, relay, hub_time)'
                            ' values (%(hub)s, %(cell)s, %(temp)s, %(sp)s, %(relay)s, %(time)s)', d)
        return 'ok'
