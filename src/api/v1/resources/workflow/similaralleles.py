from typing import List
from api.config import config
from datalayer.alleledataloader.alleledataloader import AlleleDataLoader
from sqlalchemy import and_, or_
from api import ApiError
from api.v1.resource import LogRequestResource
from api.util.util import authenticate
from flask import request
from vardb.datamodel import allele, gene, assessment


def nearby_alleles(session, allele_id: int) -> List[int]:
    query_result = session.query(allele.Allele).filter(allele.Allele.id == allele_id)
    if query_result.count() != 1:
        raise ApiError(f'Found {query_result.count()} alleles with ID "{allele_id}"')
    query_allele = query_result.one()
    assessed_allele_ids = session.query(assessment.AlleleAssessment.allele_id).filter(
        assessment.AlleleAssessment.date_superceeded.is_(None)
    )
    max_dist = config["similar_alleles"]["max_genomic_distance"]
    return (
        session.query(allele.Allele)
        .filter(
            and_(
                allele.Allele.chromosome == query_allele.chromosome,
                allele.Allele.id.in_(assessed_allele_ids),
                allele.Allele.id != query_allele.id,
                or_(
                    # query region contained
                    and_(
                        allele.Allele.start_position <= query_allele.start_position,
                        allele.Allele.open_end_position >= query_allele.open_end_position,
                    ),
                    # allele region contained within query region
                    and_(
                        allele.Allele.start_position >= query_allele.start_position,
                        allele.Allele.open_end_position <= query_allele.open_end_position,
                    ),
                    # overlapping regions
                    and_(
                        allele.Allele.start_position >= query_allele.start_position - max_dist,
                        allele.Allele.start_position < query_allele.open_end_position + max_dist,
                    ),
                    # overlapping regions
                    and_(
                        allele.Allele.open_end_position > query_allele.start_position - max_dist,
                        allele.Allele.open_end_position < query_allele.open_end_position + max_dist,
                    ),
                ),
            )
        )
        .limit(config["similar_alleles"]["max_variants"])
        .all()
    )


class SimilarAllelesResource(LogRequestResource):
    @authenticate()
    def get(self, session, genepanel_name, genepanel_version, user=None):
        # get genepanel
        genepanel_result = session.query(gene.Genepanel).filter(
            and_(
                gene.Genepanel.name == genepanel_name,
                gene.Genepanel.version == genepanel_version,
            )
        )
        if genepanel_result.count() != 1:
            raise ApiError(
                f"Found {genepanel_result.count()} genepanels machting name={genepanel_name} version={genepanel_version}"
            )
        genepanel = genepanel_result.one()
        # get input allele IDs
        arg_name: str = "allele_ids"
        if request.args.get(arg_name) is None:
            raise ApiError(f'Missing required arg "{arg_name}"')
        allele_ids = request.args.get(arg_name).split(",")
        result = {}
        for aid in allele_ids:
            result[aid] = AlleleDataLoader(session).from_objs(
                nearby_alleles(session, aid),
                genepanel=genepanel,
                include_annotation=True,
                include_custom_annotation=False,
                include_allele_assessment=True,
                include_reference_assessments=False,
            )
        return result
