FROM ubuntu:trusty

RUN apt-get update \
    && apt-get install --yes ssh \
    && rm -rf /var/lib/apt/lists/*

COPY secret/ /etc/ssh/

CMD sshd
