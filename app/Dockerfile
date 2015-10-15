FROM debian:jessie

RUN apt-get update \
    && apt-get install --yes \
            curl \
            python3 \
            python3-psycopg2 \
            uwsgi-plugin-python3 \
    && curl https://bootstrap.pypa.io/get-pip.py | python3 \
    && apt-get autoremove --yes --purge curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt
COPY requirements.txt ./
RUN pip3 install -r requirements.txt
COPY ./ app/

EXPOSE 3030
CMD ["uwsgi", \
    "--plugin", "python3", \
    "--socket", "0.0.0.0:3030", \
    "--module", "app.app:app"]
