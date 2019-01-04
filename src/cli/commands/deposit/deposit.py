import os
import logging
import json
import re
import click

from vardb.datamodel import DB, user, gene
from vardb.deposit.deposit_custom_annotations import import_custom_annotations
from vardb.deposit.deposit_references import import_references
from vardb.deposit.deposit_users import import_users, import_groups
from vardb.deposit.deposit_analysis import DepositAnalysis
from vardb.deposit.deposit_alleles import DepositAlleles
from vardb.deposit.deposit_genepanel import DepositGenepanel
from vardb.datamodel.analysis_config import AnalysisConfigData

from cli.decorators import cli_logger, session

VCF_FIELDS_RE = re.compile(
    "(?P<analysis_name>.+[.-](?P<genepanel_name>.+)[-_](?P<genepanel_version>.+))\.vcf"
)


def validate_file_exists(path):
    return os.path.isfile(path)


@click.group(help="Data deposit")
def deposit():
    pass


@deposit.command("analysis")
@click.argument("vcf", type=click.Path(exists=True))
@click.option("--ped", type=click.Path(exists=True))
@click.option("--report", type=click.Path(exists=True))
@click.option("--warnings", type=click.Path(exists=True))
@click.option("--priority", type=click.INT, default=1)
@session
@cli_logger()
def cmd_deposit_analysis(logger, session, vcf, ped=None, report=None, warnings=None, priority=None):
    """
    Deposit an analysis given input vcf.
    File should be in format of {analysis_name}.{genepanel_name}-{genepanel_version}.vcf
    """

    matches = re.match(VCF_FIELDS_RE, os.path.basename(vcf))
    da = DepositAnalysis(session)

    report_data = warnings_data = None
    if report:
        with open(report) as f:
            report_data = f.read()

    if warnings:
        with open(warnings) as f:
            warnings_data = f.read()

    analysis_config_data = AnalysisConfigData(
        vcf,
        matches.group("analysis_name"),
        matches.group("genepanel_name"),
        matches.group("genepanel_version"),
        priority,
        ped_path=ped,
        report=report_data,
        warnings=warnings_data,
    )
    analysis = da.import_vcf(analysis_config_data)
    session.commit()
    logger.echo("Analysis {} deposited successfully".format(analysis.name))


@deposit.command("exists")
@click.argument("fs", nargs=-1, type=click.Path(exists=True))
def all_exists(fs):
    click.echo("OK")


@deposit.command("alleles")
@click.argument("vcf", nargs=-1, type=click.Path(exists=True))
@click.option("--genepanel_name")
@click.option("--genepanel_version")
@session
@cli_logger()
def cmd_deposit_alleles(logger, session, vcf, genepanel_name, genepanel_version):
    """
    Deposit alleles given input vcf.

    If genepanel not given by options, get it from the filename assuming
    format of {something}.{genepanel_name}_{genepanel_version}.vcf
    """
    da = DepositAlleles(session)
    for f in vcf:
        if not genepanel_name:
            matches = re.match(VCF_FIELDS_RE, os.path.basename(f))
            genepanel_name = matches.group("genepanel_name")
            genepanel_version = matches.group("genepanel_version")
        da.import_vcf(f, genepanel_name, genepanel_version)
    session.commit()
    logger.echo("Deposited " + str(len(vcf)) + " files.")


@deposit.command("annotation")
@click.argument("vcf")
@session
@cli_logger()
def cmd_deposit_annotation(logger, session, vcf):
    """
    Update/deposit alleles with annotation only given input vcf.
    No analysis/variant interpretation is created.
    File should be in format of {something}.{genepanel_name}_{genepanel_version}.vcf
    """
    matches = re.match(VCF_FIELDS_RE, os.path.basename(vcf))
    da = DepositAlleles(session)
    da.import_vcf(
        vcf,
        matches.group("genepanel_name"),
        matches.group("genepanel_version"),
        annotation_only=True,
    )
    session.commit()
    logger.echo("Annotation imported successfully")


@deposit.command("references")
@click.argument("references_json")
@session
@cli_logger()
def cmd_deposit_references(logger, session, references_json):
    """
    Deposit/update a set of references into database given by DB_URL.

    Input is a line separated JSON file, with one reference object per line.
    """
    import_references(session, references_json)
    logger.echo("References imported successfully")


@deposit.command("custom_annotation")
@click.argument("custom_annotation_json")
@session
@cli_logger()
def cmd_deposit_custom_annotations(logger, session, custom_annotation_json):
    """
    Deposit/update a set of custom annotations into database given by DB_URL.

    Input is a line separated JSON file, with one custom annotation object per line.
    """
    import_custom_annotations(session, custom_annotation_json)
    logger.echo("Custom annotation imported successfully")


@deposit.command("genepanel")
@click.option("--genepanel_name")
@click.option("--genepanel_version")
@click.option("--transcripts_path")
@click.option("--phenotypes_path")
@click.option("--replace", is_flag=True)
@click.option("--folder", help="Folder to look for files assuming standard filenames")
@session
@cli_logger()
def cmd_deposit_genepanel(
    logger,
    session,
    genepanel_name,
    genepanel_version,
    transcripts_path,
    phenotypes_path,
    replace,
    folder,
):
    """
    Create or replace genepanel. If replacing genepanel, use --replace flag.
    """
    if folder:
        prefix = folder.split("/")[-1]
        transcripts_path = folder + "/" + prefix + ".transcripts.csv"
        phenotypes_path = folder + "/" + prefix + ".phenotypes.csv"
        genepanel_name, genepanel_version = prefix.split("_", 1)
        assert genepanel_version.startswith("v")

    dg = DepositGenepanel(session)
    dg.add_genepanel(
        transcripts_path, phenotypes_path, genepanel_name, genepanel_version, replace=replace
    )
    logger.echo("Genepanel {}_{} imported successfully".format(genepanel_name, genepanel_version))


@deposit.command("append_genepanel_to_usergroup")
@click.argument("genepanel_name", required=True)
@click.argument("genepanel_version", required=True)
@click.argument("user_group_name", required=True)
@session
@cli_logger()
def cmd_append_genepanel_to_usergroup(
    logger, session, genepanel_name, genepanel_version, user_group_name
):
    """
    Append a genepanel to the given user group.
    :param genepanel_name:
    :param genepanel_version:
    :param user_group_name:
    :return:
    """
    user_group = session.query(user.UserGroup).filter(user.UserGroup.name == user_group_name).one()

    gp = (
        session.query(gene.Genepanel)
        .filter(gene.Genepanel.name == genepanel_name, gene.Genepanel.version == genepanel_version)
        .one()
    )

    if gp in user_group.genepanels:
        logger.echo(
            "Genepanel ({gp_name},{gp_version}) already exists in user group {user_group}".format(
                gp_name=genepanel_name, gp_version=genepanel_version, user_group=user_group_name
            )
        )
        return

    user_group.genepanels.append(gp)

    session.commit()

    logger.echo(
        "Appended genepanel ({gp_name},{gp_version}) to user group {user_group}".format(
            gp_name=genepanel_name, gp_version=genepanel_version, user_group=user_group_name
        )
    )
