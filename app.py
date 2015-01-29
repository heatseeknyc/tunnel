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
    if flask.request.method == 'GET':
        cursor = db.cursor()
        cursor.execute('select * from readings order by time desc limit 100')
        return flask.render_template('readings.html', readings=cursor.fetchall())
    elif flask.request.method == 'POST':
        d = flask.request.form.copy()
        d['time'] = datetime.fromtimestamp(int(d['time']))
        db.cursor().execute('insert into readings values'
                            ' (%(hub)s, %(time)s, %(cell)s, %(temp)s)', d)
        return ''

if __name__ == '__main__':
    app.run(debug=True)
