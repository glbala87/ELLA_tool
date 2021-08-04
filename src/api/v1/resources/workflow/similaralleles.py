from typing import List, Mapping, Dict
from api.config import config
from datalayer.alleledataloader.alleledataloader import AlleleDataLoader
from sqlalchemy import and_, or_, func
from api import ApiError
from api.v1.resource import LogRequestResource
from api.util.util import authenticate
from flask import request
from vardb.datamodel import allele, gene, assessment


def get_nearby_allele_ids(session, allele_ids: List[int]) -> Mapping[int, List[int]]:
    max_dist = config["similar_alleles"]["max_genomic_distance"]

    # Create temporary table with regions to check assessed alles against
    regions = (
        session.query(
            allele.Allele.id.label("allele_id"),
            allele.Allele.chromosome,
            allele.Allele.start_position,
            allele.Allele.open_end_position,
            (allele.Allele.start_position - max_dist).label("padded_start_position"),
            (allele.Allele.open_end_position + max_dist).label("padded_open_end_position"),
        )
        .filter(allele.Allele.id.in_(allele_ids))
        .temp_table("similaralleles_region")
    )

    assessed_allele_ids = session.query(assessment.AlleleAssessment.allele_id).filter(
        assessment.AlleleAssessment.date_superceeded.is_(None)
    )

    # allele_id | assessed_allele_id |
    #         2 |                  1 |
    #         6 |                  5 |
    #         3 |                  7 |
    #         6 |                  8 |
    nearby_alleles = (
        session.query(
            regions.c.allele_id,
            allele.Allele.id.label("assessed_allele_id"),
        )
        .select_from(allele.Allele)
        .join(
            regions,
            and_(
                allele.Allele.chromosome == regions.c.chromosome,
                allele.Allele.id != regions.c.allele_id,
                or_(
                    # query region contained
                    and_(
                        allele.Allele.start_position <= regions.c.start_position,
                        allele.Allele.open_end_position >= regions.c.open_end_position,
                    ),
                    # allele region contained within query region
                    and_(
                        allele.Allele.start_position >= regions.c.start_position,
                        allele.Allele.open_end_position <= regions.c.open_end_position,
                    ),
                    # overlapping regions
                    and_(
                        allele.Allele.start_position >= regions.c.padded_start_position,
                        allele.Allele.start_position < regions.c.padded_open_end_position,
                    ),
                    # overlapping regions
                    and_(
                        allele.Allele.open_end_position > regions.c.padded_start_position,
                        allele.Allele.open_end_position < regions.c.padded_open_end_position,
                    ),
                ),
            ),
        )
        .filter(
            allele.Allele.id.in_(assessed_allele_ids),
        )
        .order_by(
            func.abs(
                (allele.Allele.start_position + allele.Allele.open_end_position) / 2
                - (regions.c.start_position + regions.c.open_end_position) / 2
            )
        )
    ).all()

    # Dictionary of query allele ids to nearby assessed allele ids
    # {
    #     2: [1],
    #     3: [7],
    #     4: [],
    #     6: [5,8],
    # }
    ret: Dict[int, List[int]] = {a_id: [] for a_id in allele_ids}
    for allele_id, assessed_allele_id in nearby_alleles:
        ret[allele_id].append(assessed_allele_id)

    # Limit the number of variants returned per allele id
    max_variants = config["similar_alleles"]["max_variants"]
    ret = {k: v[:max_variants] for k, v in ret.items()}
    return ret


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
        allele_ids = [int(x) for x in request.args.get(arg_name).split(",")]

        nearby_allele_ids = get_nearby_allele_ids(session, allele_ids)
        allele_ids_to_load = set(sum((x for x in nearby_allele_ids.values()), []))

        allele_objs = (
            session.query(allele.Allele).filter(allele.Allele.id.in_(allele_ids_to_load)).all()
        )
        loaded_alleles = AlleleDataLoader(session).from_objs(
            allele_objs,
            genepanel=genepanel,
            include_annotation=True,
            include_custom_annotation=False,
            include_allele_assessment=True,
            include_reference_assessments=False,
        )

        result = {}
        for aid_query, aids_nearby in nearby_allele_ids.items():
            # use order from nearby_allele_ids
            r = list(filter(lambda x: x["id"] in aids_nearby, loaded_alleles))
            result[str(aid_query)] = r
        return result
