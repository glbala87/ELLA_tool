from vardb.datamodel import Base
from sqlalchemy import Column, Integer, Text, Float, String, ForeignKey, Index, text, func
from sqlalchemy.dialects.postgresql import ARRAY

from api.config import config as global_config


class AnnotationShadowTranscript(Base):
    __tablename__ = "annotationshadowtranscript"

    id = Column(Integer, primary_key=True)
    allele_id = Column(Integer, ForeignKey("allele.id"), index=True)
    hgnc_id = Column(Integer, index=True)
    symbol = Column(String, index=True)
    transcript = Column(String, index=True)
    hgvsc = Column(String)
    protein = Column(String)
    hgvsp = Column(String)
    consequences = Column(ARRAY(Text))
    exon_distance = Column(Integer)
    coding_region_distance = Column(Integer)

    __table_args__ = (
        Index(
            "ix_annotationshadowtranscript_hgvsc",
            func.lower(hgvsc),
            postgresql_ops={"data": "text_pattern_ops"},
        ),
    )


def iter_freq_groups(config):
    frequency_groups = config["frequencies"]["groups"]
    for freq_group in frequency_groups:
        for freq_provider, freq_keys in frequency_groups[
            freq_group
        ].items():  # 'ExAC', ['G', 'SAS', ...]
            for freq_key in freq_keys:
                yield freq_provider, freq_key


class AnnotationShadowFrequency(Base):
    __tablename__ = "annotationshadowfrequency"

    id = Column(Integer, primary_key=True)
    allele_id = Column(Integer, ForeignKey("allele.id"), index=True)


# HACK: Done this way for integration testing purposes, where we want
# the possibility to redefine the columns globally according to a test config.
# This function lets you override the columns in this module's
# AnnotationShadowFrequency instance.
# See create_shadow_tables().
def update_annotation_shadow_columns(config):

    # Dynamically add frequency columns
    for freq_provider, freq_key in iter_freq_groups(config):
        freq_column_name = freq_provider + "." + freq_key
        freq_num_column_name = freq_provider + "_num." + freq_key

        # Add frequency
        if not hasattr(AnnotationShadowFrequency, freq_column_name):
            setattr(AnnotationShadowFrequency, freq_column_name, Column(Float))

        # Add frequency number, e.g. 'ExAC_num.SAS'
        if not hasattr(AnnotationShadowFrequency, freq_num_column_name):
            setattr(AnnotationShadowFrequency, freq_num_column_name, Column(Integer))


# By default, create using app global config
# which is what we want in production
update_annotation_shadow_columns(global_config)


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


def create_shadow_tables(session, config, create_transcript=True, create_frequency=True):
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
    update_annotation_shadow_columns(config)

    if create_transcript:
        AnnotationShadowTranscript.__table__.drop(session.connection(), checkfirst=True)
        AnnotationShadowTranscript.__table__.create(session.connection())
    if create_frequency:
        AnnotationShadowFrequency.__table__.drop(session.connection(), checkfirst=True)
        AnnotationShadowFrequency.__table__.create(session.connection())

    session.execute(create_trigger_sql(config))

    if create_transcript:
        session.execute(
            "SELECT insert_annotationshadowtranscript(allele_id, annotations) from annotation WHERE date_superceeded IS NULL"
        )
    if create_frequency:
        session.execute(
            "SELECT insert_annotationshadowfrequency(allele_id, annotations) from annotation WHERE date_superceeded IS NULL"
        )
