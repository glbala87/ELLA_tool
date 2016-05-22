#!/bin/bash
# print the url to our ella instance:

branch=$(git rev-parse --abbrev-ref HEAD)
port=$(docker port "ella-$branch-$USER" | cut -d: -f2)

OUR_DOCKER_MACHINE="osxdocker"

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


echo "Ella is running at $url"
