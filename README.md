
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

## Initial Setup
```bash
bash db/init.sh
for x in db app web tunnel; do
  docker build -t $x $x
  sudo systemctl enable $PWD/$x/$x.service
  sudo systemctl start $x.service
done
sudo systemctl enable $PWD/app/batch.service
sudo systemctl start batch.service
```

## Rebuilding
e.g. for `app`:

    docker build -t app app
    sudo systemctl restart app.service

## Connecting to the Database
Examples:
- `bash db/connect.sh`
- `bash db/connect.sh < commands.sql`
- `bash db/connect.sh pg_dump > dump.sql`

## Status and Logs

    systemctl status db app web batch
