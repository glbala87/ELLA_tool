"""vardb datamodel Allele class"""
from sqlalchemy import Column, Sequence, Integer, String, Table, ForeignKey, and_
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Index, UniqueConstraint

from vardb.datamodel import Base


class Allele(Base):
    """Represents an allele (a variant type in a genomic position)"""
    __tablename__ = "allele"

    id = Column(Integer, Sequence("id_allele_seq"), primary_key=True)
    genomeReference = Column("genome_reference", String(15), nullable=False)
    genotypes = relationship("Genotype", primaryjoin="or_(Allele.id==Genotype.allele_id, "
                                                         "Allele.id==Genotype.secondallele_id)")
    chromosome = Column(String(10), nullable=False)
    startPosition = Column("start_position", Integer, nullable=False) # TODO: Use Postgres int4range when SQLAlchemy supports it
    openEndPosition = Column("open_end_position", Integer, nullable=False)
    changeFrom = Column("change_from", String, nullable=False) # Drop argument to String(). This is only supported by Postgres and SQLite
    changeTo = Column("change_to", String, nullable=False)
    changeType = Column("change_type", String(5), nullable=False)
    vcfRef = Column("vcf_ref", String, nullable=False)
    vcfAlt = Column("vcf_alt", String, nullable=False)
    vcfPos = Column("vcf_pos", Integer, nullable=False)

    __table_args__ = (Index("ix_alleleloci", "chromosome", "start_position", "open_end_position"),
                      UniqueConstraint("chromosome", "start_position", "open_end_position", "change_from", "change_to", "change_type", name="ucAllele"), )


    def __repr__(self):
        return "<Allele('%s','%s', '%s', '%s', '%s', '%s')>" % (self.chromosome, self.startPosition,
                                                                self.openEndPosition, self.changeType,
                                                                self.changeFrom, self.changeTo)
