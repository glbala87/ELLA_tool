from api.config import config
from datalayer.alleledataloader.alleledataloader import AlleleDataLoader
from sqlalchemy import and_
from api import ApiError
from api.v1.resource import LogRequestResource
from api.util.util import authenticate
from flask import request
from vardb.datamodel import allele, gene, assessment


class SimilarAllelesResource(LogRequestResource):
    @authenticate()
    def get(self, session, genepanel_name, genepanel_version, user=None):
        # get genepanel
        genepanel = (
            session.query(gene.Genepanel)
            .filter(
                and_(
                    gene.Genepanel.name == genepanel_name,
                    gene.Genepanel.version == genepanel_version,
                )
            )
            .one()
        )
        # get input allele IDs
        arg_name: str = "allele_ids"
        if request.args.get(arg_name) is None:
            raise ApiError(f'Missing required arg "{arg_name}"')
        allele_ids = request.args.get(arg_name).split(",")
        data = {}
        for aid in allele_ids:
            query_result = session.query(allele.Allele).filter(allele.Allele.id == aid)
            if query_result.count() != 1:
                raise ApiError(f'Found {query_result.count()} alleles with ID "{aid}"')
            query_allele = query_result.one()
            assessed_allele_ids = session.query(assessment.AlleleAssessment.allele_id)
            similar_alleles = (
                session.query(allele.Allele)
                .filter(
                    and_(
                        allele.Allele.id.in_(assessed_allele_ids),
                        allele.Allele.chromosome == query_allele.chromosome,
                        # allele.Allele.start_position != query_allele.start_position,
                        allele.Allele.start_position.between(
                            query_allele.start_position
                            - config["similar_alleles"]["max_genomic_distance"],
                            query_allele.start_position
                            + config["similar_alleles"]["max_genomic_distance"],
                        ),
                    )
                )
                .limit(config["similar_alleles"]["max_variants"])
                .all()
            )
            data[aid] = AlleleDataLoader(session).from_objs(
                similar_alleles,
                genepanel=genepanel,
                include_annotation=True,
                include_custom_annotation=False,
                include_allele_assessment=True,
                include_reference_assessments=False,
            )
        return data
