import subprocess

import flask


app = flask.Flask(__name__)

@app.route('/<port>', methods=('POST',))
def execute(port):
    try:
        return subprocess.check_output([
            'ssh', '-p', port, 'localhost',
            flask.request.form['command']
        ], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        return e.output, 500
