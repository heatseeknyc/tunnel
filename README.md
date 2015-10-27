
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

`ssh -p 2222 core@setup.heatseeknyc.com`

## Initial Setup
```bash
bash db/init.sh
for x in db app web tunnel; do
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
