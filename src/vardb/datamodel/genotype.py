"""vardb datamodel Genotype class"""
from sqlalchemy import Column, Integer, Boolean, String, Enum, SmallInteger
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

from vardb.datamodel import Base
from vardb.util.mutjson import JSONMutableDict


class Genotype(Base):
    """
    Represent an observed diploid genotype for proband (i.e. an instance of a pair of alleles.)

    We only store the proband's variants in the database. Related metadata for the genotype for whole
    family is stored in genotypemetadata table.

    Genotype rows are only given for proband samples.
    """
    __tablename__ = "genotype"

    id = Column(Integer, primary_key=True)
    # Shortcut to get both alleles
    alleles = relationship("Allele", primaryjoin="or_(Allele.id==Genotype.allele_id, "
                                                 "Allele.id==Genotype.secondallele_id)", uselist=True)
    allele_id = Column(Integer, ForeignKey("allele.id"), nullable=False)
    secondallele_id = Column(Integer, ForeignKey("allele.id"))
    allele = relationship("Allele", primaryjoin=("genotype.c.allele_id==allele.c.id"))
    secondallele = relationship("Allele", primaryjoin=("genotype.c.secondallele_id==allele.c.id"))  # None, unless heterozygous nonreference
    sample_id = Column(Integer, ForeignKey("sample.id"), index=True, nullable=False)  # Proband's sample id, set for optimization only
    sample = relationship("Sample", backref='genotypes')
    filter_status = Column(String)  # FILTER
    variant_quality = Column(Integer)  # QUAL

    def __repr__(self):
        return "<Genotype('%s','%s', '%s')>" % (self.allele, self.secondallele, self.sample)


class GenotypeSampleData(Base):
    """
    Provides information for many samples in relation to one (proband) genotype.

    For biallelic genotypes (when genotype.secondallele_id is not null), there will be two entries
    per sample.

    Represents a direct translation of a (decomposed) vcf per-sample data.

    Note that we only store actual variants for proband samples,
    so this table represents metadata for other samples with regards
    to the proband's variants.

                        +-----------------------------+
                        |----------------------+      |
                        +---------------|      |      |
                        |      +---+  +---+  +-+-+  +-+-+
     GenotypeSampleData +------+GSD|  |GSD|  |GSD|  |GSD|
                        |      +-+-+  +-+-+  +-+-+  +-+-+
                        |        |      |      |      |
      +--------+   +----v----+   |      |      |      |
      | Allele +^--+Genotype |   |      |      |      |
      +--------+   +----^----+   |      |      |      |
                        |        |      |      |      |
                        |      +-v-+  +-v-+  +-v-+  +-v-+
           Samples      +------+ P |  | F |  | M |  | S |
                               +---+  +---+  +---+  +---+



    Some important specifics:
     - secondallele: Whether current entry applies to the secondallele_id in connected genotype
     - type: Given in relation to the _proband's_ variant. E.g. if a father sample is
       given as 'Reference' in regards to a proband's variant, it could also have another variant
       (that is not stored) at this site. This example would equal a '0/.' GT in the vcf.
     - multiallelic: Indicates whether this site is multiallelic in relation to the sample_id. In other words whether there's
       another variant in this location for this sample if type is given as 'Heterozygous' or 'Reference'.
       Will be set for vcf GT of '1/.' or '0/.'.
    """
    __tablename__ = "genotypesampledata"

    id = Column(Integer, primary_key=True)
    # Family samples will connect to proband's genotype_ids
    genotype_id = Column(Integer, ForeignKey("genotype.id"))
    genotype = relationship(Genotype, backref='genotypesampledata')
    secondallele = Column(Boolean)  # Whether this entry applies to the secondallele_id in genotype
    multiallelic = Column(Boolean)  # Whether the site is multiallelic for _this sample_. I.e the sample has another variant than the proband's one.
    type = Column(Enum("Homozygous", "Heterozygous", "Reference", "No coverage", name="genotypesampledata_type"))  # The sample's genotype in relation to the proband's variant.
    sample_id = Column(Integer, ForeignKey("sample.id"), index=True, nullable=False)
    genotype_quality = Column(SmallInteger)  # GQ
    sequencing_depth = Column(SmallInteger)  # DP
    genotype_likelihood = Column(ARRAY(Integer))  # PL Phred scale score for each type: [(0,0), (0,1), (1,1)]
    allele_depth = Column(JSONMutableDict.as_mutable(JSONB), default={})  # AD {'REF': 0, 'A': 23, 'G': 32}
