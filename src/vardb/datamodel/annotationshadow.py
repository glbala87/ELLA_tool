from vardb.datamodel import DB
from vardb.datamodel import Base, annotation, gene
from sqlalchemy import Column, Integer, Float, String, ForeignKey, Table
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects.postgresql import ARRAY

from api.config import config

db = DB()
db.connect()


#
# AnnotationShadowTranscript
#


class AnnotationShadowTranscript(Base):
    __tablename__ = "annotationshadowtranscript"

    id = Column(Integer, primary_key=True)
    allele_id = Column(Integer, ForeignKey("allele.id"), index=True)
    hgnc_id = Column(Integer, index=True)
    symbol = Column(String, index=True)
    transcript = Column(String, index=True)
    hgvsc = Column(String, index=True)
    hgvsp = Column(String, index=True)
    consequences = Column(ARRAY(String))
    exon_distance = Column(Integer, index=True)



ANNOTATION_SHADOW_TRANSCRIPT_TRIGGER = '''
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
                hgvsp,
                consequences,
                exon_distance
            )
            SELECT allele_id,
                   (a->>'hgnc_id')::integer,
                   a->>'symbol',
                   a->>'transcript',
                   a->>'HGVSc',
                   a->>'HGVSp',
                   ARRAY(SELECT jsonb_array_elements_text(a->'consequences')),
                   (a->>'exon_distance')::integer
            FROM jsonb_array_elements(annotations->'transcripts') as a;
    END;
$$;

CREATE OR REPLACE FUNCTION annotation_to_annotationshadowtranscript() RETURNS TRIGGER AS $annotation_to_annotationshadowtranscript$
    BEGIN
        IF (TG_OP = 'INSERT') THEN
            PERFORM insert_annotationshadowtranscript(NEW.allele_id, NEW.annotations);
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
            DELETE FROM annotationshadowtranscript WHERE allele_id = OLD.allele_id;
            RETURN OLD;
        END IF;
    END;
$annotation_to_annotationshadowtranscript$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS annotation_to_annotationshadowtranscript ON annotation;
CREATE TRIGGER annotation_to_annotationshadowtranscript
BEFORE INSERT OR UPDATE OR DELETE ON annotation
    FOR EACH ROW EXECUTE PROCEDURE annotation_to_annotationshadowtranscript();
'''


def create_annotationshadowtranscript_table(session):
    AnnotationShadowTranscript.__table__.drop(db.engine, checkfirst=True)
    AnnotationShadowTranscript.__table__.create(db.engine)
    session.execute(ANNOTATION_SHADOW_TRANSCRIPT_TRIGGER)
    session.execute('SELECT insert_annotationshadowtranscript(allele_id, annotations) from annotation')


#
# AnnotationShadowFrequency
#

class AnnotationShadowFrequency(Base):
    __tablename__ = "annotationshadowfrequency"

    id = Column(Integer, primary_key=True)
    allele_id = Column(Integer, ForeignKey("allele.id"), index=True)


def iter_freq_groups():
    frequency_groups = config['variant_criteria']['frequencies']['groups']
    for freq_group in frequency_groups:
        for freq_provider, freq_keys in frequency_groups[freq_group].iteritems():  # 'ExAC', ['G', 'SAS', ...]
            for freq_key in freq_keys:
                yield freq_provider, freq_key


# Dynamically add frequency columns
for freq_provider, freq_key in iter_freq_groups():
    # Add frequency itself
    setattr(AnnotationShadowFrequency, freq_provider + '.' + freq_key, Column(Float, index=True))
    # Add frequency number, e.g. 'ExAC_num.SAS'
    setattr(AnnotationShadowFrequency, freq_provider + '_num.' + freq_key, Column(Integer, index=True))


freq_insert_into = []
freq_values = []
for freq_provider, freq_key in iter_freq_groups():
    freq_insert_into.append('"{}.{}"'.format(freq_provider, freq_key))
    freq_insert_into.append('"{}_num.{}"'.format(freq_provider, freq_key))
    freq_values.append("(annotations->'frequencies'->'{}'->'freq'->>'{}')::float".format(freq_provider, freq_key))
    freq_values.append("(annotations->'frequencies'->'{}'->'num'->>'{}')::integer".format(freq_provider, freq_key))

ANNOTATION_SHADOW_FREQUENCY_TRIGGER = '''
CREATE OR REPLACE FUNCTION insert_annotationshadowfrequency(allele_id INTEGER, annotations JSONB) RETURNS void
LANGUAGE plpgsql
AS $$
    BEGIN
        INSERT INTO annotationshadowfrequency
            (
                allele_id,
                {insert_into}
            )
            VALUES (
                allele_id,
                {values}
            );

    END;
$$;

CREATE OR REPLACE FUNCTION annotation_to_annotationshadowfrequency() RETURNS TRIGGER AS $annotation_to_annotationshadowfrequency$
    BEGIN
        IF (TG_OP = 'INSERT') THEN
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
            DELETE FROM annotationshadowfrequency WHERE allele_id = OLD.allele_id;
            RETURN OLD;
        END IF;
    END;
$annotation_to_annotationshadowfrequency$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS annotation_to_annotationshadowfrequency ON annotation;
CREATE TRIGGER annotation_to_annotationshadowfrequency
BEFORE INSERT OR UPDATE OR DELETE ON annotation
    FOR EACH ROW EXECUTE PROCEDURE annotation_to_annotationshadowfrequency();
'''.format(insert_into=',\n'.join(freq_insert_into), values=',\n'.join(freq_values))


def create_annotationshadowfrequency_table(session):
    AnnotationShadowFrequency.__table__.drop(db.engine, checkfirst=True)
    AnnotationShadowFrequency.__table__.create(db.engine)
    session.execute(ANNOTATION_SHADOW_FREQUENCY_TRIGGER)
    session.execute('SELECT insert_annotationshadowfrequency(allele_id, annotations) from annotation')

#create_annotationshadowfrequency_table(db.session)
