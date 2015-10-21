port=5000

. dev/docker-machine.sh

set +e
docker stop app
docker stop db
docker rm app
docker rm db
set -e

docker build -t db db
docker run --name db --volumes-from db-data -d db

docker build -t app app
docker build -t app:dev dev/app

echo -e "\n###\n### Starting server at http://$(docker-machine ip $machine):$port\n###\n"
docker run --name app --link db -v "$PWD/app":/opt/app:ro -p $port:$port app:dev
