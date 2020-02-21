#!/bin/bash

ls -la | grep .coverage-
coverage combine .coverage-*
coverage report
