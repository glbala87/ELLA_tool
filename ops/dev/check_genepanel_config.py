#!/usr/bin/env python
"""
Standalone script for checking syntax of genepanel config.
"""

import argparse
import json
import os

from vardb.deposit.genepanel_config_validation import config_valid, SCHEMA_VERSION_4, SCHEMA_VERSION_3, SCHEMA_VERSION_2, SCHEMA_VERSION_1


def main():
    parser = argparse.ArgumentParser(description="Validate genepanel config")
    parser.add_argument('config_file', metavar='C', type=str,
                        help='path of config file with/without a "config" key at root')
    parser.add_argument('--schema_version', '-v', metavar='version',
                        choices=[SCHEMA_VERSION_1, SCHEMA_VERSION_2, SCHEMA_VERSION_3, SCHEMA_VERSION_4],
                        type=str, help='version of schema', required=False)

    args = parser.parse_args()

    if not os.path.exists(args.config_file):
            print "missing file " + args.config_file
            exit(1)

    with open(args.config_file) as config_file:
        config_json = json.load(config_file)
        config_data =  config_json['config'] if 'config' in config_json else config_json
        config_valid(config_data, args.schema_version)
        print "File " + args.config_file + " appears to be OK"
        exit(0)


if __name__ == '__main__':
    main()
