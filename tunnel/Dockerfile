# we use ubuntu to mimic the server that the hubs are used to connecting to
FROM ubuntu:trusty

RUN apt-get update \
    && apt-get install --yes ssh \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /var/run/sshd
COPY public/ /etc/ssh/
COPY secret/ /etc/ssh/

RUN useradd -Um hubs
COPY authorized_keys /home/hubs/.ssh/
RUN chown hubs:hubs /home/hubs/.ssh/authorized_keys
RUN chmod 600 /home/hubs/.ssh/authorized_keys

CMD ["/usr/sbin/sshd", "-D"]
