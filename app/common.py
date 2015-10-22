import os

import psycopg2
import psycopg2.extras


LIVE_SLEEP_PERIOD = (59*60 + 50) * 100  # 59m50s in centiseconds


def get_db():
    return psycopg2.connect(host=os.environ['DB_PORT_5432_TCP_ADDR'],
                            port=os.environ['DB_PORT_5432_TCP_PORT'],
                            user='postgres',
                            cursor_factory=psycopg2.extras.DictCursor)
