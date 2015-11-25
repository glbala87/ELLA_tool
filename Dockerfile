FROM debian:jessie
MAINTAINER Dave Honneffer <dave@ousamg.io>

# Standard OUSAMG Docker boilerplate
ENV DEBIAN_FRONTEND noninteractive
RUN echo "force-unsafe-io" > /etc/dpkg/dpkg.cfg.d/02apt-speedup \
    && echo "Acquire::http {No-Cache=True;};" > /etc/apt/apt.conf.d/no-cache \
    && echo "Acquire::Languages 'none';" > /etc/apt/apt.conf.d/no-lang \
    && apt-get update -qq \
    && apt-get upgrade -qq \
    && apt-get install -y locales apt-utils \
    && locale-gen C.UTF-8 \
    && /usr/sbin/update-locale LANG=C.UTF-8 \
    && apt-get remove -y locales \
    && apt-get clean && rm -rf /var/lib/apt/lists/* && rm -rf /tmp/*
ENV LANG C.UTF-8

# Our essential packages for this build go here
RUN apt-get update -qq \
    && apt-get install -f -y -q python2.7 python2.7-dev python-setuptools curl libpq-dev git build-essential postgresql-client ruby2.1 rubygems\
    && apt-get clean && rm -rf /var/lib/apt/lists/* && rm -rf /tmp/*
# NodeJS install process - this has to all run in one batch for some weird reason related to the setup app
RUN curl --silent --location https://deb.nodesource.com/setup_4.x | bash - && apt-get install -y -q nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/* && rm -rf /tmp/*

# Get pip and gulp
RUN gem install foreman
RUN curl -SL 'https://bootstrap.pypa.io/get-pip.py' | python
RUN npm install -g gulp

# Add our requirements files - honcho is a foreman clone that runs our Procfile
ADD ./requirements.txt /dist/requirements.txt
ADD ./requirements-test.txt  /dist/requirements-test.txt
ADD ./package.json /dist/package.json

# Install all our requirements for python and gulp/js
WORKDIR /dist
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-test.txt
RUN npm install

EXPOSE 5000
WORKDIR /genap
RUN mkdir /logs /static /socket
# We add our source folder for testing/deployment - this gets bashed by the volume in development
ADD . /genap
