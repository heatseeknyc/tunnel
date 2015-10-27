port=5000

. dev/docker-machine.sh

set +e
docker stop app
docker stop db
docker rm app
docker rm db
set -e

docker build -t db db
docker build -t db:dev dev/db
docker run --name db --volumes-from db-data -d db:dev

docker build -t app app
docker build -t app:dev dev/app

while ! bash db/connect.sh psql -c select; do
    sleep 1
done

version=$(awk '/^.set version / {print $3}' db/schema.sql)
if [[ $(bash db/connect.sh psql -tc '"select version from version"' < /dev/null | awk '{print $1}') != $version ]]; then
    # schema is not latest version, so start over
    docker rm db-data
    . db/init.sh
    . dev/run.sh
fi

echo -e "\n###\n### Starting server at http://$(docker-machine ip $machine):$port\n###\n"
exec docker run --name app --link db -v "$PWD/app":/opt/app:ro -p $port:$port app:dev
