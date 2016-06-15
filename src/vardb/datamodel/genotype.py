"""vardb datamodel Genotype class"""
from sqlalchemy import Column, Sequence, Integer, Boolean, String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from vardb.datamodel import Base

from vardb.util.mutjson import MUTJSONB

class Genotype(Base):
    """Represent an observed diploid geneotype (i.e. an instance of a pair of alleles.)"""
    __tablename__ = "genotype"

    id = Column(Integer, Sequence("id_genotype_seq"), primary_key=True)
    # Shortcut to get both alleles
    alleles = relationship("Allele", primaryjoin="or_(Allele.id==Genotype.allele_id, "
                                                 "Allele.id==Genotype.secondallele_id)", uselist=True)
    allele_id = Column(Integer, ForeignKey("allele.id"), nullable=False)
    secondallele_id = Column(Integer, ForeignKey("allele.id"))
    allele = relationship("Allele", primaryjoin=("genotype.c.allele_id==allele.c.id"))
    secondallele = relationship("Allele", primaryjoin=("genotype.c.secondallele_id==allele.c.id")) # None, if not hetrozygous nonreference
    homozygous = Column(Boolean, nullable=False)
    sample_id = Column(Integer, ForeignKey("sample.id"), index=True, nullable=False)
    sample = relationship("Sample", backref='genotypes')
    analysis_id = Column(Integer, ForeignKey("analysis.id"), index=True, nullable=False)
    analysis = relationship("Analysis", backref='genotypes')
    genotypeQuality = Column("genotype_quality", Integer)
    sequencingDepth = Column("sequencing_depth", Integer)
    variantQuality = Column("variant_quality", Integer) # Assume integer, not floating point
    alleleDepth = Column("allele_depth", MUTJSONB, default={})  # {'A': 23, 'G': 32}  Gives depth per allele
    filterStatus = Column("filter_status", String)

    def __repr__(self):
        return "<Genotype('%s','%s', '%s', '%s')>" % (self.allele, self.secondallele, self.homozygous, self.sample)


