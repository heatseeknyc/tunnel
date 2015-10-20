machine=relay-dev

set -ex

docker-machine start $machine
eval $(docker-machine env --shell bash $machine)
