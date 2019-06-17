"""vardb datamodel Genotype class"""
from sqlalchemy import Column, Integer, Boolean, String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from vardb.datamodel.migration.migration_base import Base
from vardb.util.mutjson import JSONMutableDict


class Genotype(Base):
    """Represent an observed diploid genotype (i.e. an instance of a pair of alleles.)"""

    __tablename__ = "genotype"

    id = Column(Integer, primary_key=True)
    # Shortcut to get both alleles
    alleles = relationship(
        "Allele",
        primaryjoin="or_(Allele.id==Genotype.allele_id, " "Allele.id==Genotype.secondallele_id)",
        uselist=True,
    )
    allele_id = Column(Integer, ForeignKey("allele.id"), nullable=False)
    secondallele_id = Column(Integer, ForeignKey("allele.id"))
    allele = relationship("Allele", primaryjoin=("genotype.c.allele_id==allele.c.id"))
    secondallele = relationship(
        "Allele", primaryjoin=("genotype.c.secondallele_id==allele.c.id")
    )  # None, if not hetrozygous nonreference
    homozygous = Column(Boolean, nullable=False)
    sample_id = Column(Integer, ForeignKey("sample.id"), index=True, nullable=False)
    sample = relationship("Sample", backref="genotypes")
    analysis_id = Column(Integer, ForeignKey("analysis.id"), index=True, nullable=False)
    analysis = relationship("Analysis", backref="genotypes")
    genotype_quality = Column(Integer)
    sequencing_depth = Column(Integer)
    variant_quality = Column(Integer)  # Assume integer, not floating point
    allele_depth = Column(
        JSONMutableDict.as_mutable(JSONB), default={}
    )  # {'A': 23, 'G': 32}  Gives depth per allele
    filter_status = Column(String)

    def __repr__(self):
        return "<Genotype('%s','%s', '%s', '%s')>" % (
            self.allele,
            self.secondallele,
            self.homozygous,
            self.sample,
        )
