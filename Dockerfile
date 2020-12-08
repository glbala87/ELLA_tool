# bionic = 18.04
FROM ubuntu:bionic-20200219 AS base
MAINTAINER OUS AMG <ella-support@medisin.uio.no>

ENV DEBIAN_FRONTEND noninteractive
ENV LANGUAGE C.UTF-8
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN echo 'Acquire::ForceIPv4 "true";' | tee /etc/apt/apt.conf.d/99force-ipv4

# Install as much as reasonable in one go to reduce image size
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gettext-base \
    python3.7 \
    make \
    bash \
    libpq5 \
    less \
    nano \
    nginx-light \
    postgresql-client \
    iotop \
    htop \
    imagemagick \
    parallel \
    ghostscript && \
    echo "Cleanup:" && \
    apt-get clean && \
    apt-get autoclean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /usr/share/doc/* /usr/share/man/* /usr/share/groff/* /usr/share/info/* /tmp/* /var/cache/apt/* /root/.cache

# Add user
RUN useradd -ms /bin/bash ella-user
RUN mkdir -p /dist /logs /data /pg-data /socket && chown -R ella-user:ella-user /dist /logs /socket /data /pg-data

# Tab completion for ella-cli
ENV PATH=/ella/bin:${PATH}
RUN echo 'eval "$(_ELLA_CLI_COMPLETE=source ella-cli)"' >> /home/ella-user/.bashrc

####
# dev image
# (also compiles files for production)
####

FROM base AS dev

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    chromium-browser \
    chromium-chromedriver \
    curl \
    fontconfig \
    gcc \
    git \
    gnupg2 \
    graphviz \
    libffi-dev \
    libpq-dev \
    make \
    openssh-client \
    postgresql \
    postgresql-contrib \
    python3-venv \
    python3.7-dev \
    python3.7-venv \
    unzip && \
    echo "Additional tools:" && \
    echo "Node v10.x:" && \
    curl -sL https://deb.nodesource.com/setup_10.x | bash - && \
    apt-get install -yqq nodejs && \
    echo "Yarn:" && \
    curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - && echo "deb http://dl.yarnpkg.com/debian/ stable main" > /etc/apt/sources.list.d/yarn.list && \
    apt-get -yqq update && apt-get install -yqq yarn


# Add our requirements files
COPY --chown=ella-user:ella-user  ./Pipfile.lock /dist/Pipfile.lock

USER ella-user

# Standalone python
RUN cd /dist && \
    WORKON_HOME="/dist" python3.7 -m venv ella-python && \
    /dist/ella-python/bin/pip install --no-cache-dir pipenv==2020.8.13 && \
    VIRTUAL_ENV=/dist/ella-python /dist/ella-python/bin/pipenv sync --dev

# Patch supervisor, so "Clear log" is not available from UI
RUN sed -i -r "s/(actions = \[)(.*?)(, clearlog)(.*)/\1\2\4/g" /dist/ella-python/lib/python3.7/site-packages/supervisor/web.py

ENV PATH="/dist/ella-python/bin:${PATH}"
ENV PYTHONPATH="/ella/src:${PYTHONPATH}"

COPY --chown=ella-user:ella-user ./package.json /dist/package.json
COPY --chown=ella-user:ella-user ./yarn.lock /dist/yarn.lock

RUN cd /dist &&  \
    yarn install --frozen-lockfile --non-interactive && \
    yarn cache clean

# See .dockerignore for files that won't be copied
COPY --chown=ella-user:ella-user . /ella

RUN rm -rf /ella/node_modules && ln -s /dist/node_modules /ella/

ENV PGHOST="/socket"
ENV PGDATA="/pg-data"
WORKDIR /ella

CMD supervisord -c /ella/ops/dev/supervisor.cfg

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
