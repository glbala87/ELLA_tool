"""varDB datamodel classes for Gene and Transcript"""
from sqlalchemy import Column, Sequence, Integer, String, Table, Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.schema import ForeignKeyConstraint

from vardb.datamodel import Base
from vardb.util.mutjson import MUTJSONB


class Gene(Base):
    """Represents a gene abstraction"""
    __tablename__ = "gene"

    hugoSymbol = Column(String(20), primary_key=True)
    ensemblGeneID = Column(String(15), unique=True)
    # dominance = Column(String(20))

    def __repr__(self):
        return "<Gene('%s')>" % self.hugoSymbol


class Transcript(Base):
    """Represents a gene transcript"""
    __tablename__ = "transcript"

    id = Column(Integer, Sequence("id_transcript_seq"), primary_key=True)
    gene_id = Column(String(20), ForeignKey("gene.hugoSymbol"), nullable=False)
    gene = relationship("Gene", lazy="joined")
    refseqName = Column(String(15), unique=True)
    ensemblID = Column(String(15), unique=True)
    genomeReference = Column(String(15), nullable=False)
    chromosome = Column(String(10), nullable=False)
    txStart = Column(Integer, nullable=False)  # TODO: Use Postgres int4range when SQLAlchemy supports it
    txEnd = Column(Integer, nullable=False)
    strand = Column(String(1), nullable=False)
    cdsStart = Column(Integer, nullable=False)  # TODO: Use Postgres int4range when SQLAlchemy supports it
    cdsEnd = Column(Integer, nullable=False)
    exonStarts = Column("exon_starts", ARRAY(Integer), nullable=False) # giving dimensions does not work
    exonEnds = Column("exon_ends", ARRAY(Integer), nullable=False)

    def __repr__(self):
        return "<Transcript('%s','%s', '%s', '%s', '%s', '%s')>" % (self.gene, self.refseqName, self.chromosome, self.txStart, self.txEnd, self.strand)

    def __str__(self):
        return "%s, %s, %s, %s, %s, %s" % (self.gene, self.refseqName, self.chromosome, self.txStart, self.txEnd, self.strand)



# Association table uses ForeignKeyContraint for referencing composite primary key in gene panel.
genepanel_transcript = Table("genepanel_transcript", Base.metadata,
                          Column("genepanel_name", String(40)),
                          Column("genepanel_version", String(5)),
                          Column("transcript_id", Integer, ForeignKey("transcript.id")),
                          ForeignKeyConstraint(["genepanel_name", "genepanel_version"], ["genepanel.name", "genepanel.version"]))


class Genepanel(Base):
    """Represents a gene panel"""
    __tablename__ = "genepanel"

    name = Column(String(40), primary_key=True)
    version = Column(String(5), primary_key=True)
    genomeReference = Column(String(15), nullable=False)
    transcripts = relationship("Transcript", secondary=genepanel_transcript, lazy='joined')
    phenotypes = relationship("Phenotype", lazy='joined')

    config = Column(MUTJSONB, default={})


    def __repr__(self):
        return "<Genepanel('%s','%s', '%s')" % (self.name, self.version, self.genomeReference)

    def __str__(self):
        return '_'.join((self.name, "OUS", "medGen", self.version, self.genomeReference))

    @staticmethod
    def create_or_update_genepanel(session, name, version, genomeRef, transcripts):
        """Add or update an existing gene panel.

        No special rules for this for now.
        session.merge will create or update db object by primary keys.
        """
        g = Genepanel(name, version, genomeRef, transcripts)
        g = session.merge(g)
        return g


class Phenotype(Base):
    """Represents a phenotype linked to a particular genepanel.
    A phenotype can have some panel specific information (like related clinical tests)
    so we link it to specific panel. So a phenotype will typically appear mulitple times
    in the table, each belonging to different panels.
    """
    __tablename__ = "phenotype"

    id = Column(Integer, Sequence("id_phenotype_seq"), primary_key=True)

    genepanelName = Column(String(40), nullable=False)
    genepanelVersion = Column(String(10), nullable=False)
    genepanel = relationship("Genepanel", uselist=False)

    gene_id = Column(String(20), ForeignKey("gene.hugoSymbol"), nullable=False)
    gene = relationship("Gene", lazy="joined")

    description = Column(String(250), nullable=False)
    inheritance = Column(String(20), nullable=False)
    inheritance_info = Column(String(200), nullable=True)
    comment = Column(String(200), nullable=True)

    # composite foreign key
    # http://docs.sqlalchemy.org/en/latest/core/constraints.html#sqlalchemy.schema.ForeignKeyConstraint:
    __table_args__ = (ForeignKeyConstraint([genepanelName, genepanelVersion], ["genepanel.name", "genepanel.version"],
                                           deferrable=True, initially="DEFERRED")
                      ,)

    def __repr__(self):
        return "<Phenotype('%s')>" % self.description[:20]
