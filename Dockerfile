# focal = 20.04
FROM ubuntu:focal-20230126 AS base
LABEL maintainer="OUS AMG <ella-support@medisin.uio.no>"

ENV DEBIAN_FRONTEND=noninteractive \
    LANGUAGE=C.UTF-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

RUN echo 'Acquire::ForceIPv4 "true";' | tee /etc/apt/apt.conf.d/99force-ipv4

ENV POSTGRES_VERSION 14
# Install as much as reasonable in one go to reduce image size
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    bash \
    curl \
    gettext-base \
    ghostscript \
    git \
    gnupg2 \
    htop \
    imagemagick \
    iotop \
    less \
    jq \
    libpq5 \
    make \
    nano \
    nginx-light \
    parallel \
    software-properties-common \
    tzdata && \
    echo "Python:" && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get -yqq update && apt-get install -yqq python3.11 python3.11-dev python3.11-venv && \
    echo "Postgres:" && \
    sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt focal-pgdg main" > /etc/apt/sources.list.d/pgdg.list' && \
    curl -sS https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    apt-get -yqq update && apt-get install -y postgresql-client-${POSTGRES_VERSION} \
    && echo "Cleanup:" && \
    apt-get clean && \
    apt-get autoclean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /usr/share/doc/* /usr/share/man/* /usr/share/groff/* /usr/share/info/* /tmp/* /var/cache/apt/* /root/.cache

# Add user
RUN useradd -ms /bin/bash ella-user
RUN mkdir -p /dist /logs /data /pg-data /socket && chown -R ella-user:ella-user /dist /logs /socket /data /pg-data

# Tab completion for ella-cli
ENV PATH=/dist/ella-python/bin:/ella/bin:${PATH} \
    PYTHONPATH=/ella/src \
    VIRTUAL_ENV=/dist/ella-python
RUN echo 'eval "$(_ELLA_CLI_COMPLETE=source ella-cli)"' >> /home/ella-user/.bashrc

RUN mkdir -p /data/fixtures/genepanels /data/analyses/incoming /data/analyses/imported /data/attachments /data/igv-data && \
    chown ella-user:ella-user /data/fixtures/genepanels /data/analyses/incoming /data/analyses/imported /data/attachments /data/igv-data

# git safedir: https://github.blog/2022-04-12-git-security-vulnerability-announced/
COPY --chown=ella-user:ella-user .gitlab/gitconfig /home/ella-user/.gitconfig

ENV ATTACHMENT_STORAGE=/data/attachments \
    ANALYSES_INCOMING=/data/analyses/incoming \
    ANALYSES_PATH=/data/analyses/imported \
    IGV_DATA=/data/igv-data

####
# dev image
# (also compiles files for production)
####

FROM base AS dev

WORKDIR /dist

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    fontconfig \
    gcc \
    graphviz \
    libffi-dev \
    libpq-dev \
    make \
    openssh-client \
    postgresql-${POSTGRES_VERSION} \
    postgresql-contrib-${POSTGRES_VERSION} \
    unzip \
    vim \
    # Chrome dependencies
    libatk-bridge2.0-0 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxkbcommon0 \
    libnss3 \
    && echo "Additional tools:" && \
    echo "Node v10.x:" && \
    curl -sL https://deb.nodesource.com/setup_10.x | bash - && \
    apt-get install -yqq nodejs && \
    echo "Yarn:" && \
    curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - && echo "deb http://dl.yarnpkg.com/debian/ stable main" > /etc/apt/sources.list.d/yarn.list && \
    apt-get -yqq update && apt-get install -yqq yarn && \
    echo "chromium: " && \
    curl -L https://www.googleapis.com/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F1105487%2Fchrome-linux.zip?alt=media > chrome_linux.zip && \
    unzip chrome_linux.zip && \
    ln -s /dist/chrome-linux/chrome /usr/bin/chrome && \
    rm chrome_linux.zip && \
    echo "chromedriver: " && \
    curl -L https://www.googleapis.com/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F1105487%2Fchromedriver_linux64.zip?alt=media > chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    ln -s /dist/chromedriver_linux64/chromedriver /usr/bin/chromedriver && \
    rm chromedriver_linux64.zip


# Add our requirements files

USER ella-user

COPY --chown=ella-user:ella-user ./package.json /dist/package.json
COPY --chown=ella-user:ella-user ./yarn.lock /dist/yarn.lock

RUN yarn install --frozen-lockfile --non-interactive && \
    yarn cache clean

USER ella-user
# Standalone python
COPY --chown=ella-user:ella-user  ./Pipfile.lock /dist/Pipfile.lock
RUN WORKON_HOME="/dist" python3.11 -m venv ella-python && \
    /dist/ella-python/bin/pip install --no-cache-dir pipenv && \
    /dist/ella-python/bin/pipenv sync --dev

# Patch supervisor, so "Clear log" is not available from UI
RUN sed -i -r "s/(actions = \[)(.*?)(, clearlog)(.*)/\1\2\4/g" /dist/ella-python/lib/python3.11/site-packages/supervisor/web.py

# See .dockerignore for files that won't be copied
COPY --chown=ella-user:ella-user . /ella

RUN rm -rf /ella/node_modules && ln -s /dist/node_modules /ella/

RUN mkdir -p /home/ella-user/.ssh /home/ella-user/.vscode-server && \
    echo "gitlab.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAfuCHKVTjquxvt6CM6tdG4SLp1Btn/nOeHHE5UOzRdf" >> /home/ella-user/.ssh/known_hosts && \
    echo "gitlab.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCsj2bNKTBSpIYDEGk9KxsGh3mySTRgMtXL583qmBpzeQ+jqCMRgBqB98u3z++J1sKlXHWfM9dyhSevkMwSbhoR8XIq/U0tCNyokEi/ueaBMCvbcTHhO7FcwzY92WK4Yt0aGROY5qX2UKSeOvuP4D6TPqKF1onrSzH9bx9XUf2lEdWT/ia1NEKjunUqu1xOB/StKDHMoX4/OKyIzuS0q/T1zOATthvasJFoPrAjkohTyaDUz2LN5JoH839hViyEG82yB+MjcFV5MU3N1l1QL3cVUCh93xSaua1N85qivl+siMkPGbO5xR/En4iEY6K2XPASUEMaieWVNTRCtJ4S8H+9" >> /home/ella-user/.ssh/known_hosts && \
    echo "gitlab.com ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBFSMqzJeV9rUzU4kWitGjeR4PWSa29SPqJ1fVkhtj3Hw9xjLVXVYrU9QlYWrOLXBpQ6KWjbjTDTdDkoohFzgbEY=" >> /home/ella-user/.ssh/known_hosts



ENV PGHOST="/socket" \
    PGDATA="/pg-data"
WORKDIR /ella

ENV ATTACHMENT_STORAGE="/ella/ella-testdata/testdata/attachments" \
    DB_URL="postgresql:///postgres" \
    DEV_IGV_CYTOBAND="https://s3.amazonaws.com/igv.broadinstitute.org/genomes/seq/b37/b37_cytoband.txt" \
    DEV_IGV_FASTA="https://s3.amazonaws.com/igv.broadinstitute.org/genomes/seq/1kg_v37/human_g1k_v37_decoy.fasta" \
    ELLA_CONFIG="/ella/ella-testdata/testdata/example_config.yml" \
    IGV_DATA="/ella/ella-testdata/testdata/igv-data" \
    PGDATA="/pg-data" \
    PGHOST="/socket" \
    PORT="5000" \
    PRODUCTION="false"

CMD ["supervisord", "-c", "/ella/ops/dev/supervisor.cfg"]

####
# production image
####

FROM dev AS production-build

RUN cd /ella && yarn build && yarn docs

FROM base AS production

USER root
COPY --from=production-build --chown=ella-user:ella-user /dist /dist
COPY --from=production-build --chown=ella-user:ella-user /ella /ella

USER ella-user
WORKDIR /ella
CMD ["/ella/ops/prod/entrypoint.sh"]

####
# review image: part prod, part dev
####

FROM production AS review

USER root
COPY --from=dev --chown=ella-user:ella-user /pg-data /pg-data
COPY --from=dev --chown=ella-user:ella-user /usr/share/postgresql /usr/share/postgresql
COPY --from=dev --chown=ella-user:ella-user /usr/share/postgresql-common /usr/share/postgresql-common
COPY --from=dev --chown=ella-user:ella-user /usr/lib/postgresql /usr/lib/postgresql

USER ella-user
# set demo defaults here, so demo/review apps can just `docker run -d`
ENV ATTACHMENT_STORAGE="/ella/ella-testdata/testdata/attachments" \
    DB_URL="postgresql:///postgres" \
    DEV_IGV_CYTOBAND="https://s3.amazonaws.com/igv.broadinstitute.org/genomes/seq/b37/b37_cytoband.txt" \
    DEV_IGV_FASTA="https://s3.amazonaws.com/igv.broadinstitute.org/genomes/seq/1kg_v37/human_g1k_v37_decoy.fasta" \
    ELLA_CONFIG="/ella/ella-testdata/testdata/example_config.yml" \
    IGV_DATA="/ella/ella-testdata/testdata/igv-data/" \
    PGDATA="/pg-data" \
    PGHOST="/socket" \
    PORT="5000" \
    PRODUCTION="false"
WORKDIR /ella
CMD ["supervisord", "-c" , "/ella/ops/demo/supervisor.cfg"]

#####
# Default is production
#####
FROM production
