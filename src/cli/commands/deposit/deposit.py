import click
import logging
import json

from vardb.datamodel import DB
from vardb.deposit.deposit_custom_annotations import import_custom_annotations
from vardb.deposit.deposit_references import import_references
from vardb.deposit.deposit_users import import_users


@click.group(help='Data deposit')
def deposit():
    pass


@deposit.command('references')
@click.argument('references_json')
def cmd_deposit_references(references_json):
    """
    Deposit/update a set of references into database given by DB_URL.

    Input is a line separated JSON file, with one reference object per line.
    """
    logging.basicConfig(level=logging.INFO)

    db = DB()
    db.connect()
    import_references(db.session, references_json)


@deposit.command('custom_annotation')
@click.argument('custom_annotation_json')
def cmd_deposit_custom_annotations(custom_annotation_json):
    """
    Deposit/update a set of custom annotations into database given by DB_URL.

    Input is a line separated JSON file, with one custom annotation object per line.
    """
    logging.basicConfig(level=logging.INFO)

    db = DB()
    db.connect()
    import_custom_annotations(db.session, custom_annotation_json)

@deposit.command('users')
@click.argument('users_json')
def cmd_deposit_users(users_json):
    """
    Deposit/update a set of users into database given by DB_URL.

    Input is a json file, with an array of user objects.

    Any user matching 'username' key will have it's record updated,
    otherwise a new record is inserted.
    """
    logging.basicConfig(level=logging.INFO)

    with open(users_json) as fd:
        users = json.load(fd)

    if not users:
        raise RuntimeError("No users found in file {}".format(users_json))

    db = DB()
    db.connect()

    import_users(db.session, users)


