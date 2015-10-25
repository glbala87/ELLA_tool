FROM debian:jessie
MAINTAINER Dave Honneffer <dave@ousamg.io>

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update -q && apt-get upgrade -q

RUN apt-get update && \
    apt-get install -y locales && \
    locale-gen C.UTF-8 && \
    /usr/sbin/update-locale LANG=C.UTF-8 && \
    apt-get remove -y locales
ENV LANG C.UTF-8

RUN apt-get install -f -y -q python2.7 python2.7-dev python-setuptools curl libpq-dev git build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && rm -rf /tmp/*
RUN curl --silent --location https://deb.nodesource.com/setup_4.x | bash - && apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && rm -rf /tmp/*

RUN curl -SL 'https://bootstrap.pypa.io/get-pip.py' | python
RUN npm install -g gulp

ADD ./requirements.txt /dist/requirements.txt
RUN echo "honcho" >> /dist/requirements.txt
ADD ./gulpfile.js /dist/gulpfile.js

WORKDIR /dist
RUN pip install --no-cache-dir -r requirements.txt
RUN npm install gulp gulpfile-install
RUN /dist/node_modules/.bin/gulpfile-install

EXPOSE 5000
WORKDIR /genap
