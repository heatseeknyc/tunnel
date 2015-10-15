import os

import psycopg2
import psycopg2.extras

def get_db():
    return psycopg2.connect(host=os.environ['DB_PORT_5432_TCP_ADDR'],
                            port=os.environ['DB_PORT_5432_TCP_PORT'],
                            user='postgres',
                            cursor_factory=psycopg2.extras.DictCursor)
