from datetime import datetime
import logging; logging.basicConfig(level=logging.INFO)

import flask
import psycopg2

app = flask.Flask(__name__)

db = psycopg2.connect(host='localhost', user='webdb', password='password')

@app.teardown_request
def teardown_request(exception):
    logging.error(exception)
    if exception:
        db.rollback()
    else:
        db.commit()

@app.route('/')
def index():
    return 'Hello, cruel world!'

@app.route('/readings', methods=('GET', 'POST'))
def readings():
    if flask.request.method == 'POST':
        d = flask.request.form.copy()
        d['time'] = datetime.fromtimestamp(int(d['time']))
        db.cursor().execute('insert into readings values'
                            ' (%(hub)s, %(time)s, %(cell)s, %(temp)s)', d)
        return 'ok'
    elif flask.request.method == 'GET':
        cursor = db.cursor()
        cursor.execute('select * from readings order by time desc limit 100')
        return flask.render_template('readings.html', readings=cursor.fetchall())

@app.route('/hubs', methods=('GET', 'POST'))
def hubs():
    if flask.request.method == 'POST':
        db.cursor().execute('insert into hubs values'
                            ' (%(hub)s, %(port)s)', flask.request.form)
        return 'ok'
    elif flask.request.method == 'GET':
        cursor = db.cursor()
        cursor.execute('select * from hubs order by time desc limit 100')
        return flask.render_template('hubs.html', hubs=cursor.fetchall())

if __name__ == '__main__':
    app.run(debug=True)
