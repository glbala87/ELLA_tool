#!/usr/bin/env python
"""
Standalone script for checking syntax of genepanel config.
"""

import argparse
import json
import os

from vardb.deposit.genepanel_config_validation import config_valid


def main():
    parser = argparse.ArgumentParser(description="Validate genepanel config")
    parser.add_argument('config_file', metavar='C', type=str,
                        help='path of config file with/without a "config" key at root')
    args = parser.parse_args()

    if not os.path.exists(args.config_file):
            print "missing file " + args.config_file
            exit(1)

    with open(args.config_file) as config_file:
        config_json = json.load(config_file)
        config_valid(config_json['config']) if 'config' in config_json else config_valid(config_json)
        print "File " + args.config_file + " appears to be OK"
        exit(0)


if __name__ == '__main__':
    main()
