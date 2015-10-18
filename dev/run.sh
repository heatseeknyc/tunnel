port=5000

set -x

. dev/stop.sh

docker build -t db db
docker build -t app app
docker build -t app:dev dev/app

docker run --name db --volumes-from db-data -d db
echo -e "\n###\n### Starting server at http://$(docker-machine ip $machine):$port\n###\n"
docker run --name app --link db -v "$PWD/app":/opt/app:ro -p $port:$port app:dev
