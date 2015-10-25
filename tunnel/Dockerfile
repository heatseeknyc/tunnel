# we use ubuntu to mimic the server that the hubs are already used to connecting to
FROM ubuntu:trusty

RUN apt-get update \
    && apt-get install --yes ssh \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /var/run/sshd
COPY public/ /etc/ssh/
COPY secret/ /etc/ssh/

CMD ["/usr/sbin/sshd", "-D"]
