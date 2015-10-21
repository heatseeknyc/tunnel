
command="$*"
if [ "$command" == "" ]; then
    command=psql
fi

if [ -t 0 ]; then  # stdin is a terminal
    terminal="-t"
fi

set -x

docker run --link db --rm -i $terminal postgres:9 sh -c "exec $command -h \"\$DB_PORT_5432_TCP_ADDR\" -p \"\$DB_PORT_5432_TCP_PORT\" -U postgres"
