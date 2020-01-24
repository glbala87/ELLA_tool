from typing import List, Optional, Dict
from sqlalchemy.orm import aliased
from sqlalchemy.sql.schema import Table
from sqlalchemy import literal, and_
from vardb.util.extended_query import ExtendedQuery
from vardb.datamodel import genotype, allele, sample


def extend_genotype_table_with_allele(session, genotype_table: Table) -> ExtendedQuery:
    genotype_with_allele = session.query(
        allele.Allele.chromosome.label("chromosome"),
        allele.Allele.start_position.label("start_position"),
        allele.Allele.open_end_position.label("open_end_position"),
        allele.Allele.genome_reference.label("genome_reference"),
        *[c for c in genotype_table.c],
    ).join(genotype_table, genotype_table.c.allele_id == allele.Allele.id)
    return genotype_with_allele


def get_genotype_temp_table(
    session,
    allele_ids: List[int],
    sample_ids: List[int],
    genotype_extras: Optional[Dict] = None,
    genotypesampledata_extras: Optional[Dict] = None,
):
    """
    Creates a combined genotype table (query)
    which looks like the following:

    -------------------------------------------------------------------------------------
    | allele_id | sample_1_type  | sample_1_sex | sample_2_type  | sample_2_sex | ...
    -------------------------------------------------------------------------------------
    | 55        | 'Heterozygous' | 'Male'       | 'Heterozygous' | 'Female'     | ...
    | 71        | 'Homozygous'   | 'Male'       | 'Heterozygous' | 'Female'     | ...
    | 82        | 'Heterozygous' | 'Male'       | 'Heterozygous' | 'Female'     | ...
    | 91        | 'Heterozygous' | 'Male'       | 'Heterozygous' | 'Female'     | ...
    ...

    The data is created by combining the genotype and genotypesampledata tables,
    for all provided samples.

    :note: All samples must belong to same analysis.
    :note: allele_id and secondallele_id are union'ed together into one table.
    """

    assert (
        session.query(sample.Sample.analysis_id)
        .filter(sample.Sample.id.in_(sample_ids))
        .distinct()
        .count()
        == 1
    ), "All sample ids must belong to same analysis"

    if genotype_extras is None:
        genotype_extras = {}

    if genotypesampledata_extras is None:
        genotypesampledata_extras = {}

    def create_query(secondallele=False):

        samples = session.query(sample.Sample).filter(sample.Sample.id.in_(sample_ids)).all()

        # We'll join several times on same table, so create aliases for each sample
        aliased_genotypesampledata = dict()
        sample_fields = list()
        for s in samples:
            aliased_genotypesampledata[s.id] = aliased(genotype.GenotypeSampleData)
            sample_fields.extend(
                [
                    aliased_genotypesampledata[s.id].id.label(f"{s.id}_genotypeid"),
                    aliased_genotypesampledata[s.id].type.label(f"{s.id}_type"),
                    literal(s.sex).label(f"{s.id}_sex"),
                    *[
                        getattr(genotype.Genotype, field).label(f"{s.id}_{key}")
                        for key, field in genotype_extras.items()
                    ],
                    *[
                        getattr(aliased_genotypesampledata[s.id], field).label(f"{s.id}_{key}")
                        for key, field in genotypesampledata_extras.items()
                    ],
                ]
            )

        if secondallele:
            allele_id_field = genotype.Genotype.secondallele_id
        else:
            allele_id_field = genotype.Genotype.allele_id

        genotype_query = session.query(allele_id_field.label("allele_id"), *sample_fields).filter(
            allele_id_field.in_(allele_ids), genotype.Genotype.sample_id.in_(sample_ids)
        )

        for sample_id, gsd in aliased_genotypesampledata.items():
            genotype_query = genotype_query.outerjoin(
                gsd,
                and_(
                    genotype.Genotype.id == gsd.genotype_id,
                    gsd.secondallele.is_(secondallele),
                    gsd.sample_id == sample_id,
                ),
            )

        return genotype_query

    # Combine allele_id and secondallele_id into one large table
    without_secondallele = create_query(False)
    with_secondallele = create_query(True)

    genotype_query = without_secondallele.union(with_secondallele).subquery()
    genotype_query = session.query(genotype_query)

    genotype_table = genotype_query.temp_table("genotype_query")

    assert session.query(genotype_table.c.allele_id.distinct()).count() == len(allele_ids)
    return genotype_table
