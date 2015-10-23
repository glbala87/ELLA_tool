FROM debian:jessie
MAINTAINER Dave Honneffer <dave@ousamg.io>

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update -q && apt-get upgrade -q
RUN apt-get install -f -y python2.7 python2.7-dev python-pip python-setuptools curl build-essential libpq-dev git
RUN curl --silent --location https://deb.nodesource.com/setup_4.x | bash - && apt-get install -y nodejs
# RUN apt-get clean && rm -rf /var/lib/apt/lists/* && rm -rf /tmp/*
RUN npm install --global gulp gulp-concat gulp-uglify gulp-flatten gulp-babel gulp-livereload gulp-wrapper gulp-less gulp-plumber gulp-notify

ADD ./requirements.txt /genap/requirements.txt
VOLUME /genap
WORKDIR /genap

RUN pip install -r requirements.txt
