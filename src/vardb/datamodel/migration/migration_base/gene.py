"""varDB datamodel classes for Gene and Transcript"""
from sqlalchemy import Column, Integer, String, Enum, Table
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.schema import ForeignKeyConstraint

from vardb.datamodel.migration.migration_base import Base
from vardb.util.mutjson import JSONMutableDict


class Gene(Base):
    """Represents a gene abstraction"""

    __tablename__ = "gene"

    hgnc_id = Column(Integer, primary_key=True)
    hgnc_symbol = Column(String(), unique=True, nullable=False)
    ensembl_gene_id = Column(String(15), unique=True)
    omim_entry_id = Column(Integer)

    def __repr__(self):
        return "<Gene(%d, '%s')>" % (self.hgnc_id, self.hgnc_symbol)


class Transcript(Base):
    """Represents a gene transcript"""

    __tablename__ = "transcript"

    id = Column(Integer, primary_key=True)
    gene_id = Column(Integer, ForeignKey("gene.hgnc_id"), nullable=False)
    gene = relationship("Gene", lazy="joined")
    transcript_name = Column(String(), unique=True, nullable=False)
    type = Column(Enum("RefSeq", "Ensembl", "LRG", name="transcript_type"), nullable=False)
    corresponding_refseq = Column(String())
    corresponding_ensembl = Column(String())
    corresponding_lrg = Column(String())
    genome_reference = Column(String(), nullable=False)
    chromosome = Column(String(), nullable=False)
    tx_start = Column(Integer, nullable=False)
    tx_end = Column(Integer, nullable=False)
    strand = Column(String(1), nullable=False)
    cds_start = Column(Integer, nullable=False)
    cds_end = Column(Integer, nullable=False)
    exon_starts = Column(ARRAY(Integer), nullable=False)  # giving dimensions does not work
    exon_ends = Column(ARRAY(Integer), nullable=False)

    def __repr__(self):
        return "<Transcript('%s','%s', '%s', '%s', '%s', '%s')>" % (
            self.gene,
            self.transcript_name,
            self.chromosome,
            self.tx_start,
            self.tx_end,
            self.strand,
        )

    def __str__(self):
        return "%s, %s, %s, %s, %s, %s" % (
            self.gene,
            self.transcript_name,
            self.chromosome,
            self.tx_start,
            self.tx_end,
            self.strand,
        )


# Association table uses ForeignKeyContraint for referencing composite primary key in gene panel.
genepanel_transcript = Table(
    "genepanel_transcript",
    Base.metadata,
    Column("genepanel_name", nullable=False),
    Column("genepanel_version", nullable=False),
    Column("transcript_id", Integer, ForeignKey("transcript.id"), nullable=False),
    ForeignKeyConstraint(
        ["genepanel_name", "genepanel_version"],
        ["genepanel.name", "genepanel.version"],
        ondelete="CASCADE",
    ),
)


class Genepanel(Base):
    """Represents a gene panel"""

    __tablename__ = "genepanel"

    name = Column(String(), primary_key=True)
    version = Column(String(), primary_key=True)
    genome_reference = Column(String(15), nullable=False)
    transcripts = relationship("Transcript", secondary=genepanel_transcript)
    phenotypes = relationship("Phenotype")

    # TODO: Is it possible to validate against schema as part of __init__?
    # format defined by genepanel-config-schema_v2.json
    config = Column(JSONMutableDict.as_mutable(JSONB), default={})

    def __repr__(self):
        return "<Genepanel('%s','%s', '%s')" % (self.name, self.version, self.genome_reference)

    def __str__(self):
        return "_".join((self.name, self.version, self.genome_reference))


class Phenotype(Base):
    """Represents a phenotype linked to a particular genepanel.
    A phenotype can have some panel specific information (like related clinical tests)
    so we link it to specific panel. So a phenotype will typically appear mulitple times
    in the table, each belonging to different panels.
    """

    __tablename__ = "phenotype"

    id = Column(Integer, primary_key=True)

    genepanel_name = Column(String(40), nullable=False)
    genepanel_version = Column(String(10), nullable=False)
    genepanel = relationship("Genepanel", uselist=False)

    gene_id = Column(Integer, ForeignKey("gene.hgnc_id"), nullable=False)
    gene = relationship("Gene", lazy="joined")

    description = Column(String(250), nullable=False)
    inheritance = Column(String(20), nullable=False)
    inheritance_info = Column(String(200), nullable=True)
    omim_id = Column(Integer, nullable=True)
    pmid = Column(Integer, nullable=True)
    comment = Column(String(200), nullable=True)

    # composite foreign key
    # http://docs.sqlalchemy.org/en/latest/core/constraints.html#sqlalchemy.schema.ForeignKeyConstraint:
    __table_args__ = (
        ForeignKeyConstraint(
            [genepanel_name, genepanel_version],
            ["genepanel.name", "genepanel.version"],
            deferrable=True,
            initially="DEFERRED",
        ),
    )

    @staticmethod
    def clean_inheritance_code(code):
        if not code:
            return code
        return code.replace(";", "")

    def __repr__(self):
        return "<Phenotype('%s')>" % self.description[:20]
