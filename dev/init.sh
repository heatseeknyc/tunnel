machine=relay-dev

set -x

brew install docker docker-machine

if ! docker-machine start $machine; then
    docker-machine create --driver virtualbox $machine
fi
eval $(docker-machine env --shell bash $machine)

. db/init.sh
. dev/run.sh
