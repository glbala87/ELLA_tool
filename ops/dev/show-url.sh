#!/bin/bash

# print the url to our ella instance
# usage: show-url.sh [container] Assumes default container name if none is given


defaultContainer="ella-$(git rev-parse --abbrev-ref HEAD)-$USER" # see Makefile
container=${1:-$defaultContainer} # use $defaultContainer if $1 is not set

# echo "Finding http port used by container $container assuming it's in range [8000,>"
port=$(docker port "$container" | cut -d: -f2 | grep 80)

if [[ "$port" == "" ]]
then
    echo "Docker error. I'm out!"
    exit 1
fi

if [[ $DOCKER_MACHINE_NAME == "" ]] # Assumes native docker
then
    url="http://localhost:$port"
else
    url="http://$(docker-machine ip $DOCKER_MACHINE_NAME):$port"
fi


echo "$url"
