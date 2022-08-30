import os
import re
from pathlib import Path
import click
from sqlalchemy.orm.session import Session

from vardb.datamodel import user, gene
from vardb.deposit.deposit_custom_annotations import import_custom_annotations
from vardb.deposit.deposit_references import import_references
from vardb.deposit.deposit_analysis import DepositAnalysis
from vardb.deposit.deposit_alleles import DepositAlleles
from vardb.deposit.deposit_genepanel import DepositGenepanel
from vardb.deposit.analysis_config import AnalysisConfigData

from cli.decorators import cli_logger, session

VCF_FIELDS_RE = re.compile(
    r"(?P<analysis_name>.+[.-](?P<genepanel_name>.+)[-_](?P<genepanel_version>.+))\.vcf"
)


def validate_file_exists(path):
    return os.path.isfile(path)


@click.group(help="Data deposit")
def deposit():
    pass


@deposit.command("analysis")
@click.argument("file_or_folder", type=click.Path(exists=True))
@session
@cli_logger()
def cmd_deposit_analysis(logger, session, file_or_folder):
    """
    Deposit an analysis given input vcf.
    File should be in format of {analysis_name}.{genepanel_name}-{genepanel_version}.vcf
    """

    da = DepositAnalysis(session)
    analysis_config_data = AnalysisConfigData(file_or_folder)
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
@click.argument("references_json", type=click.Path(exists=True))
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
@click.option("--genepanel_name", type=str)
@click.option("--genepanel_version", type=str)
@click.option("--transcripts_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--phenotypes_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--replace", is_flag=True)
@click.option(
    "--folder",
    help="Folder to look for files assuming standard filenames",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@session
@cli_logger()
def cmd_deposit_genepanel(
    logger,
    session: Session,
    genepanel_name: str,
    genepanel_version: str,
    transcripts_path: Path,
    phenotypes_path: Path,
    replace: bool,
    folder: Path,
):
    """
    Create or replace genepanel. If replacing genepanel, use --replace flag.
    """
    if not folder and not (
        genepanel_name and genepanel_version and transcripts_path and phenotypes_path
    ):
        raise RuntimeError(
            "Need to provide either a folder containing gene panel files or gene panel files + name/version"
        )
    if folder:
        prefix = folder.parts[-1]
        transcripts_path = folder / Path(prefix + "_genes_transcripts_regions.tsv")
        phenotypes_path = folder / Path(prefix + "_phenotypes.tsv")
        genepanel_name, genepanel_version = prefix.split("_", 1)
        assert re.match(
            r"^v\d+\.\d$", genepanel_version
        ), f"Expected gene panel version to be of format vXX.X, found ${genepanel_version}"
        assert genepanel_version.startswith("v")

    dg = DepositGenepanel(session)
    dg.add_genepanel(
        transcripts_path, phenotypes_path, genepanel_name, genepanel_version, replace=replace
    )


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
