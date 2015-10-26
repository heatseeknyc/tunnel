# we use ubuntu to mimic the server that the hubs are used to connecting to
FROM ubuntu:trusty

RUN apt-get update && \
    apt-get install --yes \
            curl \
            python3 \
            ssh \
            uwsgi-plugin-python3 \
            && \
    curl https://bootstrap.pypa.io/get-pip.py | python3 && \
    apt-get autoremove --yes --purge curl && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /var/run/sshd
COPY public/ /etc/ssh/
COPY secret/ /etc/ssh/

RUN useradd -Um hubs
COPY authorized_keys /home/hubs/.ssh/
RUN chown hubs:hubs /home/hubs/.ssh/authorized_keys
RUN chmod 600 /home/hubs/.ssh/authorized_keys

WORKDIR /opt/tunnel
COPY requirements.txt ./
RUN pip3 install -r requirements.txt
COPY ./ ./

EXPOSE 80
CMD /usr/sbin/sshd && \
    uwsgi \
          --plugin python3 \
          --http-socket 0.0.0.0:80 \
          --module app:app \
