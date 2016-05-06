#!/bin/bash
# print the url to our ella instance:
url="http://$(docker-machine ip osxdocker):$(docker port ella-588-inheritance-erikseve | cut -d: -f2)"

echo "Ella is running at $url"
