FROM debian:jessie
MAINTAINER Dave Honneffer <dave@ousamg.io>

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update -q && apt-get upgrade -q
RUN apt-get install -f -y python2.7 python2.7-dev python-setuptools curl build-essential libpq-dev git
RUN curl -SL 'https://bootstrap.pypa.io/get-pip.py' | python
RUN curl --silent --location https://deb.nodesource.com/setup_4.x | bash - && apt-get install -y nodejs
RUN apt-get clean && rm -rf /var/lib/apt/lists/* && rm -rf /tmp/*
RUN npm install -g gulp

ADD ./requirements.txt /dist/requirements.txt
ADD ./gulpfile.js /dist/gulpfile.js

WORKDIR /dist
RUN pip install --no-cache-dir -r requirements.txt
RUN npm install gulp gulpfile-install
RUN /dist/node_modules/.bin/gulpfile-install

WORKDIR /genap
