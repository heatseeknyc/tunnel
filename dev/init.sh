set -ex

brew update
brew install docker docker-machine

docker-machine create --driver virtualbox relay-dev

. dev/docker-machine.sh
. db/init.sh
