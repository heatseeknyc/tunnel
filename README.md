
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

`ssh -p 2222 core@setup.heatseeknyc.com`

### Adding an SSH Key

`update-ssh-keys -a <name> < key.pem`

## Initial Setup
Until we change the hub firmware to tunnel through a custom ssh port, we have to [change the CoreOS ssh port](https://coreos.com/os/docs/latest/customizing-sshd.html) to get out of the way. Currently we use 2222.

Ask a friend for the files to put in `tunnel/secret/`. Then:

```bash
bash db/init.sh
for x in db tunnel app web; do
  docker build -t $x $x
  sudo systemctl enable $PWD/$x/$x.service
  sudo systemctl start $x
done
sudo systemctl enable $PWD/app/batch.service
sudo systemctl start batch
```

## Rebuilding
e.g. for `app`:

    docker build -t app app
    sudo systemctl restart app

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
