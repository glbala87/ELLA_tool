FROM debian:jessie
MAINTAINER Dave Honneffer <dave@ousamg.io>

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update -q && apt-get upgrade -q
RUN apt-get install -f -y python2.7 python2.7-dev python-pip python-setuptools curl build-essential libpq-dev git
RUN curl --silent --location https://deb.nodesource.com/setup_4.x | bash - && apt-get install -y nodejs
RUN apt-get clean && rm -rf /var/lib/apt/lists/* && rm -rf /tmp/*
ADD ./requirements.txt /dist/requirements.txt
ADD ./gulpfile.js /dist/gulpfile.js
RUN cd /dist && pip install -r requirements.txt
RUN cd /dist && npm install gulp gulpfile-install
RUN cd /dist && /dist/node_modules/.bin/gulpfile-install

WORKDIR /genap
