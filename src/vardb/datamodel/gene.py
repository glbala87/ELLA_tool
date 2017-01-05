"""varDB datamodel classes for Gene and Transcript"""
from sqlalchemy import Column, Sequence, Integer, String, Table, Enum, UniqueConstraint
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.schema import ForeignKeyConstraint

from vardb.datamodel import Base
from vardb.util.mutjson import JSONMutableDict


class Gene(Base):
    """Represents a gene abstraction"""
    __tablename__ = "gene"

    hugo_symbol = Column(String(), primary_key=True)
    ensembl_gene_id = Column(String(15), unique=True)
    # dominance = Column(String(20))

    def __repr__(self):
        return "<Gene('%s')>" % self.hugo_symbol


class Transcript(Base):
    """Represents a gene transcript"""
    __tablename__ = "transcript"
    __table_args__ = (
        UniqueConstraint('refseq_name', 'ensembl_id', name='transcript_unique'),

    )

    id = Column(Integer, Sequence("id_transcript_seq"), primary_key=True)
    gene_id = Column(String(20), ForeignKey("gene.hugo_symbol"), nullable=False)
    gene = relationship("Gene", lazy="joined")
    refseq_name = Column(String(15))
    ensembl_id = Column(String(15))
    genome_reference = Column(String(15), nullable=False)
    chromosome = Column(String(10), nullable=False)
    tx_start = Column(Integer, nullable=False)
    tx_end = Column(Integer, nullable=False)
    strand = Column(String(1), nullable=False)
    cds_start = Column(Integer, nullable=False)
    cds_end = Column(Integer, nullable=False)
    exon_starts = Column(ARRAY(Integer), nullable=False) # giving dimensions does not work
    exon_ends = Column(ARRAY(Integer), nullable=False)

    @staticmethod
    def get_name(name):
        """

        :param name:
        :return: the name with version stripped off
        """
        return name.split('.', 1)[0] if '.' in name else name

    def get_unversioned_name(self):
        return Transcript.get_name(self.refseq_name)

    def __repr__(self):
        return "<Transcript('%s','%s', '%s', '%s', '%s', '%s')>" % (self.gene, self.refseq_name, self.chromosome, self.tx_start, self.tx_end, self.strand)

    def __str__(self):
        return "%s, %s, %s, %s, %s, %s" % (self.gene, self.refseq_name, self.chromosome, self.tx_start, self.tx_end, self.strand)



# Association table uses ForeignKeyContraint for referencing composite primary key in gene panel.
genepanel_transcript = Table("genepanel_transcript", Base.metadata,
                          Column("genepanel_name"),
                          Column("genepanel_version"),
                          Column("transcript_id", Integer, ForeignKey("transcript.id")),
                          ForeignKeyConstraint(["genepanel_name", "genepanel_version"], ["genepanel.name", "genepanel.version"]))


class Genepanel(Base):
    """Represents a gene panel"""
    __tablename__ = "genepanel"

    name = Column(String(), primary_key=True)
    version = Column(String(), primary_key=True)
    genome_reference = Column(String(15), nullable=False)
    transcripts = relationship("Transcript", secondary=genepanel_transcript, lazy='joined')
    phenotypes = relationship("Phenotype", lazy='joined')

    config = Column(JSONMutableDict.as_mutable(JSONB), default={})  # format defined by


    def __repr__(self):
        return "<Genepanel('%s','%s', '%s')" % (self.name, self.version, self.genome_reference)

    def __str__(self):
        return '_'.join((self.name, self.version, self.genome_reference))

    def find_inheritance(self, symbol):
        if not self.phenotypes:
            return None

        return map(lambda ph: Phenotype.clean_inheritance_code(ph.inheritance), filter(lambda ph: symbol == ph.gene_id, self.phenotypes))


    @staticmethod
    def create_or_update_genepanel(session, name, version, genome_ref, transcripts):
        """Add or update an existing gene panel.

        No special rules for this for now.
        session.merge will create or update db object by primary keys.
        """
        g = Genepanel(name, version, genome_ref, transcripts)
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

    genepanel_name = Column(String(40), nullable=False)
    genepanel_version = Column(String(10), nullable=False)
    genepanel = relationship("Genepanel", uselist=False)

    gene_id = Column(String(20), ForeignKey("gene.hugo_symbol"), nullable=False)
    gene = relationship("Gene", lazy="joined")

    description = Column(String(250), nullable=False)
    inheritance = Column(String(20), nullable=False)
    inheritance_info = Column(String(200), nullable=True)
    omim_id = Column(Integer, nullable=True)
    pmid = Column(Integer, nullable=True)
    comment = Column(String(200), nullable=True)

    # composite foreign key
    # http://docs.sqlalchemy.org/en/latest/core/constraints.html#sqlalchemy.schema.ForeignKeyConstraint:
    __table_args__ = (ForeignKeyConstraint([genepanel_name, genepanel_version], ["genepanel.name", "genepanel.version"],
                                           deferrable=True, initially="DEFERRED")
                      ,)

    @staticmethod
    def clean_inheritance_code(code):
        if not code:
            return code
        return code.replace(';', '')


    def __repr__(self):
        return "<Phenotype('%s')>" % self.description[:20]
