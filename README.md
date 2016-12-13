# NOTE

The relay server is now deployed on Heroku [(repo located here)](https://github.com/heatseeknyc/relay),
so the majority of the code in this repository is no longer used.

The only functionality that cannot be replicated on Heroku is the SSH tunneling, so this
server is still deployed on Digital Ocean with the web facing services disabled.

The domain is now `tunnel.heatseek.org`.


# Development, on a Mac

## Initial Setup

    bash dev/init.sh

## Running

    bash dev/run.sh
    …
    bash dev/stop.sh

## Connecting to the Database
Examples:
- `bash dev/db.sh`
- `bash dev/db.sh < commands.sql`
- `bash dev/db.sh pg_dump > dump.sql`


# Production, on CoreOS

## Connecting

`ssh -p 2222 core@tunnel.heatseeknyc.com`

### Adding an SSH Key

`update-ssh-keys -a <name> < key.pem`

## Initial Setup
Until we change the hub firmware to tunnel through a custom ssh port, we have to [change the CoreOS ssh port](https://coreos.com/os/docs/latest/customizing-sshd.html) to get out of the way. Currently we use 2222.

Ask a friend for the files to put in `tunnel/secret/`. Then:

```bash
bash db/init.sh
for x in db tunnel app web; do
  docker build --pull --tag=$x $x
  sudo systemctl enable $PWD/$x/$x.service
  sudo systemctl start $x
done
sudo systemctl enable $PWD/app/batch.service
sudo systemctl start batch
```

## Rebuilding
For most modules, e.g. for `web`:

    docker build --pull --tag web web
    sudo systemctl restart web

### Rebuilding the Batch Module
The `batch` module shares a lot of code with the `app` module, so they use the same docker image:

    docker build --pull --tag app app
    sudo systemctl restart batch

## Connecting to the Database
Examples:
- `bash db/connect.sh`
- `bash db/connect.sh < commands.sql`
- `bash db/connect.sh pg_dump > dump.sql`

## Status and Logs

    systemctl status db tunnel app web batch
    journalctl -ru web

## Connecting to a Hub

    docker exec -it tunnel ssh -p <port> localhost

## Debugging Tunnel Ports

    docker exec tunnel netstat -a | grep ssh
