FROM ousamg/gin:latest
MAINTAINER Dave Honneffer <dave@ousamg.io>

# Install gulp and karma-cli globally
RUN npm install -g gulp
RUN npm install -g karma-cli

# Add our requirements files
ADD ./requirements.txt /dist/requirements.txt
ADD ./requirements-test.txt  /dist/requirements-test.txt
ADD ./package.json /dist/package.json

# Install all our requirements for python and gulp/js
WORKDIR /dist
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-test.txt
RUN npm install

# We add our source folder for testing/deployment - this gets bashed by the volume in development
ADD . /genap
WORKDIR /genap
