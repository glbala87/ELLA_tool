# aka debian:stretch
FROM debian:9.2 AS base
MAINTAINER OUS AMG <ella-support@medisin.uio.no>

ENV DEBIAN_FRONTEND noninteractive
ENV LANGUAGE C.UTF-8
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN echo 'Acquire::ForceIPv4 "true";' | tee /etc/apt/apt.conf.d/99force-ipv4

# Install as much as reasonable in one go to reduce image size
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    python \
    make \
    bash \
    libpq5 \
    supervisor \
    less \
    nano \
    nginx-light \
    iotop \
    htop \
    imagemagick \
    ghostscript && \
    apt-get clean && \
    apt-get autoclean && \
    echo "Cleanup:" && \
    rm -rf /var/lib/apt/lists/* && \
    cp -R /usr/share/locale/en\@* /tmp/ && rm -rf /usr/share/locale/* && mv /tmp/en\@* /usr/share/locale/ && \
    rm -rf /usr/share/doc/* /usr/share/man/* /usr/share/groff/* /usr/share/info/* /tmp/* /var/cache/apt/* /root/.cache

RUN useradd -ms /bin/bash ella-user
RUN mkdir -p /dist /logs /data /pg-data /socket && chown -R ella-user:ella-user /dist /logs /socket /data /pg-data


####
# dev image
# (also compiles files for production)
####

FROM base AS dev

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gnupg2 \
    python-dev \
    make \
    build-essential \
    git \
    curl \
    gcc \
    unzip \
    ca-certificates \
    postgresql \
    postgresql-contrib \
    postgresql-client \
    libpq-dev \
    libffi-dev \
    fontconfig && \
    echo "Additional tools:" && \
    curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - && echo "deb http://dl.yarnpkg.com/debian/ stable main" > /etc/apt/sources.list.d/yarn.list && \
    curl -sLk https://deb.nodesource.com/setup_8.x | bash - && \
    apt-get install -y -q nodejs yarn && \
    curl -SLk 'https://bootstrap.pypa.io/get-pip.py' | python && \
    curl -L https://github.com/tianon/gosu/releases/download/1.7/gosu-amd64 -o /usr/local/bin/gosu && chmod u+x /usr/local/bin/gosu && \
	echo "Google Chrome:" && \
	curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb https://dl-ssl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && \
	apt-get -yqq update && \
    apt-get -yqq install google-chrome-stable && \
    echo "Chromedriver:" && \
    curl -L -O https://chromedriver.storage.googleapis.com/2.44/chromedriver_linux64.zip && unzip -d /usr/local/bin chromedriver_linux64.zip && rm chromedriver_linux64.zip


# Add our requirements files
COPY ./requirements.txt /dist/requirements.txt
COPY ./requirements-test.txt  /dist/requirements-test.txt
COPY ./requirements-prod.txt  /dist/requirements-prod.txt

# pip
RUN cd /dist && \
    pip install virtualenv && \
    WORKON_HOME="/dist" virtualenv ella-python && \
    /dist/ella-python/bin/pip install --no-cache-dir -r requirements.txt && \
    /dist/ella-python/bin/pip install --no-cache-dir -r requirements-test.txt && \
    /dist/ella-python/bin/pip install --no-cache-dir -r requirements-prod.txt

ENV PATH="/dist/ella-python/bin:${PATH}"
ENV PYTHONPATH="/ella/src:${PYTHONPATH}"

# npm
# changes to package.json does a fresh install as Docker won't use it's cache
COPY ./package.json /dist/package.json
COPY ./yarn.lock /dist/yarn.lock

USER ella-user

RUN cd /dist &&  \
    yarn install && \
    yarn cache clean

USER root
# See .dockerignore for files that won't be copied
COPY . /ella
# Older docker doesn't support --chown
RUN chown ella-user:ella-user -R /ella

USER ella-user
RUN rm -rf /ella/node_modules && ln -s /dist/node_modules /ella/

ENV PGHOST="/socket"
WORKDIR /ella


####
# production image
####

FROM dev AS production-build

RUN cd /ella && yarn production

FROM base AS production

USER root
COPY --from=production-build /dist/ella-python /dist/ella-python
RUN chown ella-user:ella-user -R /dist

ENV PATH="/dist/ella-python/bin:${PATH}"
ENV PYTHONPATH="/ella/src:${PYTHONPATH}"

COPY --from=production-build /ella /ella
RUN chown ella-user:ella-user -R /ella

USER ella-user
ENTRYPOINT ['/ella/ops/prod/entrypoint.sh']

#####
# Default is production
#####
FROM production
