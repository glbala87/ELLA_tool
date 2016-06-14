import os
import sys
import glob
import json
import openpyxl

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
EXCELDOC = sys.argv[1]


CODES = [
    'PV',
    'PS',
    'PM',
    'PP',
    'BP',
    'BS',
    'BA',
    'REQ'
]


def print_metadata(input):
    wb = openpyxl.load_workbook(input)

    sheet = wb['ACMG criteria']

    data = dict()

    for row in sheet.rows:
        code = row[0].value
        # Only use rows with actual codes
        if not any(code.startswith(c) for c in CODES):
            continue

        data[code] = {
            'short_criteria': row[1].value,
            'sources': []
        }
        if row[2].value:
            data[code]['criteria'] = row[2].value
        if row[3].value:
            data[code]['notes'] = row[3].value
        if row[5].value:
            data[code]['sources'] = [v.strip() for v in row[5].value.split(',')]
            data[code]['sources'] = [c for c in data[code]['sources'] for r in CODES if c.startswith(r)]

    print json.dumps(data, indent=4)


print_metadata(EXCELDOC)
