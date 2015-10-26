# "Heat Seek OS" was built with connections to an old relay server running Ubuntu 14.04,
# which unfortunately means hubs now expect an outdated key type (ecdsa-sha2-nistp256)
# so we have to stick to the same openssh version
# which is most easily accomplished by continuing to use Ubuntu 14.04
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

# identify ourselves as the host that hubs expect:
COPY sshd/ /etc/ssh/
COPY secret/sshd/ /etc/ssh/

# authorize hubs to log in as user 'hubs':
RUN useradd -Um hubs
COPY ssh/authorized_keys /home/hubs/.ssh/
RUN chown hubs:hubs /home/hubs/.ssh/authorized_keys
RUN chmod 600 /home/hubs/.ssh/authorized_keys

# use a key trusted by hubs when ssh'ing back into them:
COPY ssh/id_rsa.pub /root/.ssh/
COPY secret/ssh/id_rsa /root/.ssh/
RUN chmod 600 /root/.ssh/id_rsa

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
