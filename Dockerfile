FROM ousamg/ella.core:0.9.2
MAINTAINER Dave Honneffer <dave@ousamg.io>

# Get gulp
RUN npm install -g gulp

# Add our requirements files
COPY ./requirements.txt /dist/requirements.txt
COPY ./requirements-test.txt  /dist/requirements-test.txt
COPY ./package.json /dist/package.json

# Install all our requirements for python and gulp/js
WORKDIR /dist
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-test.txt
RUN npm install

# Test builds depend on the next line
# COPY . /ella
WORKDIR /ella
