"""vardb datamodel Allele class"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Index, UniqueConstraint

from vardb.datamodel.migration.ci_migration_base import Base


class Allele(Base):
    """Represents an allele (a variant type in a genomic position)"""
    __tablename__ = "allele"

    FREQUENCY = 'FREQUENCY'
    INTRON = 'INTRON'
    GENE = 'GENE'

    id = Column(Integer, primary_key=True)
    genome_reference = Column(String, nullable=False)
    genotypes = relationship("Genotype", primaryjoin="or_(Allele.id==Genotype.allele_id, "
                                                         "Allele.id==Genotype.secondallele_id)")
    chromosome = Column(String, nullable=False)
    start_position = Column(Integer, nullable=False)
    open_end_position = Column(Integer, nullable=False)
    change_from = Column(String, nullable=False)
    change_to = Column(String, nullable=False)
    change_type = Column(String, nullable=False)
    vcf_pos = Column(Integer, nullable=False)
    vcf_ref = Column(String, nullable=False)
    vcf_alt = Column(String, nullable=False)

    __table_args__ = (Index("ix_alleleloci", "chromosome", "start_position", "open_end_position"),
                      UniqueConstraint("chromosome", "start_position", "open_end_position", "change_from", "change_to",
                                       "change_type", "vcf_pos", "vcf_ref", "vcf_alt", name="ucAllele"), )


    def __repr__(self):
        return "<Allele('%s','%s', '%s', '%s', '%s', '%s')>" % (self.chromosome, self.start_position,
                                                                self.open_end_position, self.change_type,
                                                                self.change_from, self.change_to)
