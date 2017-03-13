from sqlalchemy import Column, Integer, String

from vardb.datamodel.migration.ci_migration_base import Base


class User(Base):
    """Represents an assessment of one or more alleles."""
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String(), nullable=False)
    first_name = Column(String(), nullable=False)
    last_name = Column(String(), nullable=False)
