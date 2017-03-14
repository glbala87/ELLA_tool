import os
import logging
import json
import re
import click

from vardb.datamodel import DB
from vardb.deposit.deposit_custom_annotations import import_custom_annotations
from vardb.deposit.deposit_references import import_references
from vardb.deposit.deposit_users import import_users, import_groups
from vardb.deposit.deposit_analysis import DepositAnalysis
from vardb.deposit.deposit_alleles import DepositAlleles


VCF_FIELDS_RE = re.compile('(?P<analysis_name>.+\.(?P<genepanel_name>.+)_(?P<genepanel_version>.+))\.vcf')


@click.group(help='Data deposit')
def deposit():
    pass


@deposit.command('analysis')
@click.argument('vcf')
def cmd_deposit_analysis(vcf):
    """
    Deposit an analysis given input vcf.
    File should be in format of {analysis_name}.{genepanel_name}_{genepanel_version}.vcf
    """
    logging.basicConfig(level=logging.DEBUG)

    matches = re.match(VCF_FIELDS_RE, os.path.basename(vcf))
    db = DB()
    db.connect()
    da = DepositAnalysis(db.session)
    da.import_vcf(
        vcf,
        matches.group('analysis_name'),
        matches.group('genepanel_name'),
        matches.group('genepanel_version')
    )
    db.session.commit()


@deposit.command('alleles')
@click.argument('vcf')
def cmd_deposit_alleles(vcf):
    """
    Deposit alleles given input vcf.
    File should be in format of {something}.{genepanel_name}_{genepanel_version}.vcf
    """
    logging.basicConfig(level=logging.DEBUG)

    matches = re.match(VCF_FIELDS_RE, os.path.basename(vcf))
    db = DB()
    db.connect()
    da = DepositAlleles(db.session)
    da.import_vcf(
        vcf,
        matches.group('genepanel_name'),
        matches.group('genepanel_version')
    )
    db.session.commit()


@deposit.command('annotation')
@click.argument('vcf')
def cmd_deposit_annotation(vcf):
    """
    Update/deposit alleles with annotation only given input vcf.
    No analysis/variant interpretation is created.
    File should be in format of {something}.{genepanel_name}_{genepanel_version}.vcf
    """
    logging.basicConfig(level=logging.DEBUG)

    matches = re.match(VCF_FIELDS_RE, os.path.basename(vcf))
    db = DB()
    db.connect()
    da = DepositAlleles(db.session)
    da.import_vcf(
        vcf,
        matches.group('genepanel_name'),
        matches.group('genepanel_version'),
        annotation_only=True
    )
    db.session.commit()


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


@deposit.command('usergroups')
@click.argument('usergroups_json')
def cmd_deposit_usergroups(usergroups_json):
    """
    Deposit/update a set of user groups into database given by DB_URL.

    Input is a json file, with an array of user group objects.

    Any group matching 'name' key will have it's record updated,
    otherwise a new record is inserted.
    """
    logging.basicConfig(level=logging.INFO)

    with open(usergroups_json) as fd:
        groups = json.load(fd)

    if not groups:
        raise RuntimeError("No user groups found in file {}".format(usergroups_json))

    db = DB()
    db.connect()

    import_groups(db.session, groups)


