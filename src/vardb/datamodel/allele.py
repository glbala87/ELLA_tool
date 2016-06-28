"""vardb datamodel Allele class"""
from sqlalchemy import Column, Sequence, Integer, String, Table, ForeignKey, and_
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Index, UniqueConstraint

from vardb.datamodel import Base


class Allele(Base):
    """Represents an allele (a variant type in a genomic position)"""
    __tablename__ = "allele"

    id = Column(Integer, Sequence("id_allele_seq"), primary_key=True)
    genome_reference = Column(String, nullable=False)
    genotypes = relationship("Genotype", primaryjoin="or_(Allele.id==Genotype.allele_id, "
                                                         "Allele.id==Genotype.secondallele_id)")
    chromosome = Column(nullable=False)
    start_position = Column(Integer, nullable=False)
    open_end_position = Column(Integer, nullable=False)
    change_from = Column(String, nullable=False)
    change_to = Column(String, nullable=False)
    change_type = Column(nullable=False)

    __table_args__ = (Index("ix_alleleloci", "chromosome", "start_position", "open_end_position"),
                      UniqueConstraint("chromosome", "start_position", "open_end_position", "change_from", "change_to", "change_type", name="ucAllele"), )


    def __repr__(self):
        return "<Allele('%s','%s', '%s', '%s', '%s', '%s')>" % (self.chromosome, self.start_position,
                                                                self.open_end_position, self.change_type,
                                                                self.change_from, self.change_to)
