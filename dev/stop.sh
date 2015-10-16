machine=relay-dev

set -x

eval $(docker-machine env --shell bash $machine)

docker stop app
docker stop db
docker rm app
docker rm db
