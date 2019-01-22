# aka debian:stretch
FROM ubuntu:18.04 AS base
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
    gettext-base \
    python3.7 \
    make \
    bash \
    libpq5 \
    supervisor \
    less \
    nano \
    nginx-light \
    postgresql-client \
    iotop \
    htop \
    imagemagick \
    ghostscript && \
    echo "Cleanup:" && \
    apt-get clean && \
    apt-get autoclean && \
    rm -rf /var/lib/apt/lists/* && \
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
    python3.7-dev \
    python3.7-venv \
    python3-venv \
    make \
    build-essential \
    git \
    curl \
    gcc \
    unzip \
    ca-certificates \
    postgresql \
    postgresql-contrib \
    libpq-dev \
    libffi-dev \
    fontconfig \
    nodejs && \
    echo "Additional tools:" && \
    curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - && echo "deb http://dl.yarnpkg.com/debian/ stable main" > /etc/apt/sources.list.d/yarn.list && \
    apt-get update && apt-get install -y -q yarn && \
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

# Older docker doesn't support --chown
RUN chown ella-user:ella-user /dist/*
USER ella-user

# Standalone python
RUN cd /dist && \
    WORKON_HOME="/dist" python3.7 -m venv ella-python && \
    /dist/ella-python/bin/pip install --no-cache-dir -r requirements.txt && \
    /dist/ella-python/bin/pip install --no-cache-dir -r requirements-test.txt

ENV PATH="/dist/ella-python/bin:${PATH}"
ENV PYTHONPATH="/ella/src:${PYTHONPATH}"

COPY ./package.json /dist/package.json
COPY ./yarn.lock /dist/yarn.lock

USER root
RUN chown ella-user:ella-user /dist/*
USER ella-user

RUN cd /dist &&  \
    yarn install && \
    yarn cache clean

# See .dockerignore for files that won't be copied
COPY . /ella

USER root
RUN chown ella-user:ella-user -R /ella
USER ella-user

RUN rm -rf /ella/node_modules && ln -s /dist/node_modules /ella/

ENV PGHOST="/socket"
ENV PGDATA="/pg-data"
WORKDIR /ella


####
# production image
####

FROM dev AS production-build

RUN cd /ella && yarn build

FROM base AS production

USER root
COPY --from=production-build /dist/ella-python /dist/ella-python
RUN chown ella-user:ella-user -R /dist

ENV PATH="/dist/ella-python/bin:${PATH}"
ENV PYTHONPATH="/ella/src:${PYTHONPATH}"

COPY --from=production-build /ella /ella
RUN chown ella-user:ella-user -R /ella

USER ella-user
WORKDIR /ella
CMD /ella/ops/prod/entrypoint.sh

#####
# Default is production
#####
FROM production
