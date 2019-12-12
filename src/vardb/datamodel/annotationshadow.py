from vardb.datamodel import Base
from vardb.datamodel import sample, user
from sqlalchemy import Column, Integer, Text, Float, String, ForeignKey, Index, func, Table
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import mapper, class_mapper
from sqlalchemy.orm.exc import UnmappedClassError
from typing import Any

from api.config import config as global_config


# Note: not subclassing Base, this is handled by explicitly mapping below
class _AnnotationShadowTranscript(object):
    pass


# Set type Any. Mypy doesn't handle instrumented classes
AnnotationShadowTranscript: Any = _AnnotationShadowTranscript


# Note: not subclassing Base, this is handled in update_annotation_shadow_columns
class _AnnotationShadowFrequency(object):
    pass


# Set type Any. Mypy doesn't handle instrumented classes
AnnotationShadowFrequency: Any = _AnnotationShadowFrequency


def iter_freq_groups(config):
    frequency_groups = config["frequencies"]["groups"]
    for freq_group in frequency_groups:
        for freq_provider, freq_keys in frequency_groups[
            freq_group
        ].items():  # 'ExAC', ['G', 'SAS', ...]
            for freq_key in freq_keys:
                yield freq_provider, freq_key


# HACK: Done this way for integration testing purposes, where we want
# the possibility to redefine the columns globally according to a test config.
# This function lets you override the columns in this module's
# AnnotationShadowFrequency instance.
# See create_shadow_tables().
def update_annotation_shadow_columns(config):
    # Use columns from config to create mapping of AnnotationShadowFrequency
    # Note: This function does not guarantee that the mapped class matches
    # the table in the database.
    try:
        m = class_mapper(AnnotationShadowFrequency)
        m.dispose()
    except UnmappedClassError:
        # Class is not mapped yet
        pass

    if "annotationshadowfrequency" in Base.metadata.tables:
        Base.metadata.remove(Base.metadata.tables["annotationshadowfrequency"])
    annotationshadowfreqency = get_annotationshadowfrequency_table(config)
    mapper(AnnotationShadowFrequency, annotationshadowfreqency)
    AnnotationShadowFrequency.__table__ = annotationshadowfreqency


def iter_config_columns(config):
    for freq_provider, freq_key in iter_freq_groups(config):
        yield freq_provider + "." + freq_key, Float
        yield freq_provider + "_num." + freq_key, Integer


def get_annotationshadowfrequency_table(config, name="annotationshadowfrequency"):
    return Table(
        name,
        Base.metadata,
        Column("id", Integer, primary_key=True),
        Column("allele_id", ForeignKey("allele.id"), index=True),
        *[Column(c[0], c[1]) for c in iter_config_columns(config)]
    )


def get_annotationshadowtranscript_table(name="annotationshadowtranscript"):
    return Table(
        name,
        Base.metadata,
        Column("id", Integer, primary_key=True),
        Column("allele_id", Integer, ForeignKey("allele.id"), index=True),
        Column("hgnc_id", Integer, index=True),
        Column("symbol", String, index=True),
        Column("transcript", String, index=True),
        Column("hgvsc", String),
        Column("protein", String),
        Column("hgvsp", String),
        Column("consequences", ARRAY(Text)),
        Column("exon_distance", Integer),
        Column("coding_region_distance", Integer),
        Index(
            "ix_{}_hgvsc".format(name),
            func.lower(Column("hgvsc", String)),
            postgresql_ops={"data": "text_pattern_ops"},
        ),
    )


# By default, create using app global config
# which is what we want in production
update_annotation_shadow_columns(global_config)
mapper(AnnotationShadowTranscript, get_annotationshadowtranscript_table())


def check_db_consistency(session, config, subset=False):
    "Check that the config defines the same (or a subset) frequency shadow table as the current table in the database"
    column_res = session.execute(
        "select column_name from information_schema.columns where table_schema='public' and table_name='annotationshadowfrequency';"
    )
    db_column_names = set([c[0] for c in column_res]) - set(["id", "allele_id"])

    if subset:
        assert set([c[0] for c in iter_config_columns(config)]) - set(db_column_names) == set()
    else:
        assert set([c[0] for c in iter_config_columns(config)]) == set(
            db_column_names
        ), "{}\n{}".format(db_column_names, set([c[0] for c in iter_config_columns(config)]))


def create_trigger_sql(config):
    """
    Set up triggers to update annotationshadow tables upon
    changes (INSERT, UPDATE, or DELETE) to the annotation table.

    :warning: Not SQL injection safe, do not provide user input.
    """
    freq_insert_into = []
    freq_values = []
    for freq_provider, freq_key in iter_freq_groups(config):
        freq_insert_into.append('"{}.{}"'.format(freq_provider, freq_key))
        freq_insert_into.append('"{}_num.{}"'.format(freq_provider, freq_key))
        freq_values.append(
            "(annotations->'frequencies'->'{}'->'freq'->>'{}')::float".format(
                freq_provider, freq_key
            )
        )
        freq_values.append(
            "(annotations->'frequencies'->'{}'->'num'->>'{}')::integer".format(
                freq_provider, freq_key
            )
        )

    return """
    CREATE OR REPLACE FUNCTION insert_annotationshadowtranscript(allele_id INTEGER, annotations JSONB) RETURNS void
    LANGUAGE plpgsql
    AS $$
        BEGIN
            INSERT INTO annotationshadowtranscript
                (
                    allele_id,
                    hgnc_id,
                    symbol,
                    transcript,
                    hgvsc,
                    protein,
                    hgvsp,
                    consequences,
                    exon_distance,
                    coding_region_distance
                )
                SELECT allele_id,
                    (a->>'hgnc_id')::integer,
                    a->>'symbol',
                    a->>'transcript',
                    a->>'HGVSc',
                    a->>'protein',
                    a->>'HGVSp',
                    ARRAY(SELECT jsonb_array_elements_text(a->'consequences')),
                    (a->>'exon_distance')::integer,
                    (a->>'coding_region_distance')::integer
                FROM jsonb_array_elements(annotations->'transcripts') as a;
        END;
    $$;

    CREATE OR REPLACE FUNCTION insert_tmpannotationshadowtranscript(allele_id INTEGER, annotations JSONB) RETURNS void
    LANGUAGE plpgsql
    AS $$
        BEGIN
            INSERT INTO tmp_annotationshadowtranscript
                (
                    allele_id,
                    hgnc_id,
                    symbol,
                    transcript,
                    hgvsc,
                    protein,
                    hgvsp,
                    consequences,
                    exon_distance,
                    coding_region_distance
                )
                SELECT allele_id,
                    (a->>'hgnc_id')::integer,
                    a->>'symbol',
                    a->>'transcript',
                    a->>'HGVSc',
                    a->>'protein',
                    a->>'HGVSp',
                    ARRAY(SELECT jsonb_array_elements_text(a->'consequences')),
                    (a->>'exon_distance')::integer,
                    (a->>'coding_region_distance')::integer
                FROM jsonb_array_elements(annotations->'transcripts') as a;
        END;
    $$;

    CREATE OR REPLACE FUNCTION insert_annotationshadowfrequency(allele_id INTEGER, annotations JSONB) RETURNS void
    LANGUAGE plpgsql
    AS $$
        BEGIN
            INSERT INTO annotationshadowfrequency
                (
                    allele_id,
                    {frequency_insert_into}
                )
                VALUES (
                    allele_id,
                    {frequency_values}
                );

        END;
    $$;

    CREATE OR REPLACE FUNCTION insert_tmpannotationshadowfrequency(allele_id INTEGER, annotations JSONB) RETURNS void
    LANGUAGE plpgsql
    AS $$
        BEGIN
            INSERT INTO tmp_annotationshadowfrequency
                (
                    allele_id,
                    {frequency_insert_into}
                )
                VALUES (
                    allele_id,
                    {frequency_values}
                );

        END;
    $$;

    CREATE OR REPLACE FUNCTION delete_annotationshadow(al_id INTEGER) RETURNS void
    LANGUAGE plpgsql
    AS $$
        BEGIN
            DELETE FROM annotationshadowtranscript WHERE allele_id = al_id;
            DELETE FROM annotationshadowfrequency WHERE allele_id = al_id;
        END;
    $$;

    CREATE OR REPLACE FUNCTION annotation_to_annotationshadow() RETURNS TRIGGER AS $annotation_to_annotationshadow$
        BEGIN
            IF (TG_OP = 'INSERT') THEN
                PERFORM delete_annotationshadow(NEW.allele_id);
                PERFORM insert_annotationshadowtranscript(NEW.allele_id, NEW.annotations);
                PERFORM insert_annotationshadowfrequency(NEW.allele_id, NEW.annotations);
                RETURN NEW;
            ELSIF (TG_OP = 'UPDATE') THEN
                IF (
                    NEW.allele_id != OLD.allele_id OR
                    NEW.annotations != OLD.annotations OR
                    NEW.date_created != OLD.date_created
                ) THEN
                    RAISE EXCEPTION 'Update on one or more of the included columns for annotation table is disallowed';
                END IF;
                RETURN NEW;
            ELSIF (TG_OP = 'DELETE') THEN
                PERFORM delete_annotationshadow(allele_id);
                RETURN OLD;
            END IF;
        END;
    $annotation_to_annotationshadow$ LANGUAGE plpgsql;

    DROP TRIGGER IF EXISTS annotation_to_annotationshadow ON annotation;
    CREATE TRIGGER annotation_to_annotationshadow
    BEFORE INSERT OR UPDATE OR DELETE ON annotation
        FOR EACH ROW EXECUTE PROCEDURE annotation_to_annotationshadow();
    """.format(
        frequency_insert_into=",\n".join(freq_insert_into), frequency_values=",\n".join(freq_values)
    )


class MissingColumnError(AssertionError):
    pass


def _check_groups(frequency_groups, column_names=None):
    "Check that the freq_provider and key, e.g. GNOMAD_EXOMES G is represented in AnnotationShadowFrequency"
    existing_columns = set(AnnotationShadowFrequency.__table__.columns.keys()) - set(
        ["id", "allele_id"]
    )

    frequency_group_columns = set(
        c[0] for c in iter_config_columns({"frequencies": {"groups": frequency_groups}})
    )
    if frequency_group_columns - existing_columns:
        raise MissingColumnError(
            "AnnotationShadowFrequency missing column(s) {}. Fix global config, and rebuild shadow tables".format(
                ", ".join(frequency_group_columns - existing_columns)
            )
        )


def check_filterconfig(filterconfig):
    for f in filterconfig["filters"]:
        if f["name"] != "frequency":
            continue
        _check_groups(f["config"]["groups"])


def check_usergroup_config(usergroup):
    if usergroup.config is not None:
        _check_groups(usergroup.config.get("acmg", {}).get("frequency", {}).get("groups", {}))


def check_filterconfig_and_acmg_groups(session):

    filterconfigs = session.query(
        sample.FilterConfig.id, sample.FilterConfig.name, sample.FilterConfig.filterconfig
    ).filter(sample.FilterConfig.active.is_(True))
    for id, name, fc in filterconfigs:
        try:
            check_filterconfig(fc)
        except MissingColumnError:
            raise MissingColumnError(
                "Column not present used in filterconfig {} ({})".format(id, name)
            )

    usergroup_configs = session.query(user.UserGroup)

    for usergroup in usergroup_configs:
        try:
            check_usergroup_config(usergroup)
        except MissingColumnError:
            raise MissingColumnError(
                "Column not present used in the ACMG config for usergroup {} ({}).".format(
                    usergroup.id, usergroup.name
                )
            )


def create_tmp_shadow_tables(session, config, create_transcript=True, create_frequency=True):
    """
    Drops (if existing) and (re)creates the annotation shadow tables,
    along with their triggers. After they're setup, the tables
    are populated according to existing data in annotation table.

    Call this function whenever the shadow table definitions or
    frequency group config has changed, as the tables will need to be updated.

    :warning: TODO: The table recreation might not be within the same transaction
    as the rest of the incoming session (?). All actions might therefore not
    happen within one transaction.
    """
    session.execute(create_trigger_sql(config))

    conn = session.connection()
    if create_transcript:
        # AnnotationShadowTranscript.__table__.drop(session.connection(), checkfirst=True)
        # AnnotationShadowTranscript.__table__.create(session.connection())
        tmp_annotationshadowtranscript = get_annotationshadowtranscript_table(
            "tmp_annotationshadowtranscript"
        )
        tmp_annotationshadowtranscript.create(conn)
        conn.execute(
            "SELECT insert_tmpannotationshadowtranscript(allele_id, annotations) from annotation WHERE date_superceeded IS NULL"
        )

        # Remove temporary table from metadata
        Base.metadata.remove(tmp_annotationshadowtranscript)

    if create_frequency:
        # Create annotationshadowfrequency in a temp table, insert all data and overwrite existing annotationshadowfrequency table
        tmp_annotationshadowfrequency = get_annotationshadowfrequency_table(
            config, name="tmp_annotationshadowfrequency"
        )
        tmp_annotationshadowfrequency.create(conn)
        conn.execute(
            "SELECT insert_tmpannotationshadowfrequency(allele_id, annotations) from annotation WHERE date_superceeded IS NULL;"
        )

        # Remove temporary table from metadata
        Base.metadata.remove(tmp_annotationshadowfrequency)

        # Map AnnotationShadowFrequency using the same config used to refresh the table
        update_annotation_shadow_columns(config)

        # Check that all filterconfigs and usergroups' ACMG-configuration are still valid,
        # given the possible change in columns
        check_filterconfig_and_acmg_groups(session)


def create_shadow_tables(
    session, config, create_transcript=True, create_frequency=True, skip_tmp_tables=False
):
    if skip_tmp_tables:
        # Check that tmp tables are available
        res = session.execute("select table_name from information_schema.tables")
        table_names = set([r[0] for r in res.fetchall()])
        if create_transcript:
            assert "tmp_annotationshadowtranscript" in table_names
        if create_frequency:
            assert "tmp_annotationshadowfrequency" in table_names
    else:
        create_tmp_shadow_tables(session, config)

    def rename_tmp(table):
        "Drop existing table, and rename tmp-table + indexes + constraints"

        assert table in ["annotationshadowfrequency", "annotationshadowtranscript"]

        # Drop existing table, rename tmp-table, and drop tmp-insert function
        session.execute(
            "DROP TABLE IF EXISTS {table};"
            "ALTER TABLE tmp_{table} RENAME TO {table};"
            "DROP FUNCTION IF EXISTS insert_tmp{table}".format(table=table)
        )

        # Rename indexes
        for (index_name,) in session.execute(
            "SELECT indexname FROM pg_catalog.pg_indexes WHERE tablename='{}'".format(table)
        ):
            new_index_name = index_name.replace("tmp_{}".format(table), table)
            session.execute("ALTER INDEX {} RENAME TO {}".format(index_name, new_index_name))

        # Rename constraints (excluding primary key, this is renamed with table)
        for (constraint_name,) in session.execute(
            "SELECT conname FROM pg_catalog.pg_constraint as r WHERE r.conrelid = '{}'::regclass AND contype != 'p'".format(
                table
            )
        ):
            new_constraint_name = constraint_name.replace("tmp_{}".format(table), table)
            session.execute(
                "ALTER TABLE {} RENAME CONSTRAINT {} TO {}".format(
                    table, constraint_name, new_constraint_name
                )
            )

    if create_frequency:
        rename_tmp("annotationshadowfrequency")

    if create_transcript:
        rename_tmp("annotationshadowtranscript")
