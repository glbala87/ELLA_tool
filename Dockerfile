FROM ousamg/ella.core:0.9.4
MAINTAINER Dave Honneffer <dave@ousamg.io>

# Get gulp
RUN npm install -g gulp

# Add our requirements files
COPY ./requirements.txt /dist/requirements.txt
COPY ./requirements-test.txt  /dist/requirements-test.txt
COPY ./package.json /dist/package.json
COPY ./yarn.lock /dist/yarn.lock

# Install all our requirements for python and gulp/js
WORKDIR /dist
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-test.txt
RUN yarn install

# See .dockerignore for files that won't be copied
# Test builds depend on the next line
# COPY . /ella
WORKDIR /ella
