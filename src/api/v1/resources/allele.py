from typing import Any, Dict, Optional
from api import schemas
from api.config import config
from api.schemas.pydantic.v1 import validate_output
from api.schemas.pydantic.v1.resources import (
    AlleleGeneListResponse,
    AlleleListResponse,
    AnalysisListResponse,
    GenePanelListResponse,
)
from api.util.util import authenticate, link_filter, logger, paginate, rest_filter
from api.v1.resource import LogRequestResource
from datalayer import AlleleDataLoader
from flask import request
from sqlalchemy import cast, func, text
from sqlalchemy.dialects.postgresql import ARRAY, aggregate_order_by
from sqlalchemy.orm import Session
from sqlalchemy.types import Integer
from vardb.datamodel import allele, annotationshadow, gene, genotype, sample


class AlleleListResource(LogRequestResource):
    @authenticate()
    @validate_output(AlleleListResponse, paginated=True)
    @paginate
    @link_filter
    @rest_filter
    def get(
        self,
        session: Session,
        rest_filter: Optional[Dict],
        link_filter: Optional[Dict],
        **kwargs,
    ):
        """
        Loads alleles based on q={..} and link={..} for entities linked/related to those alleles.
        See decorator link_filter  and AlleleDataLoader for details about the possible values of link_filter
        Specify a genepanel to get more data included.
        Additional request parameters:
            - sample_id: Includes genotypes into the result and enables quality data in the annotation
            - annotation: Enables the annotation to filter transcripts to only show the relevant ones.
            - gp_name:
            - gp_version:

        ---
        summary: List alleles
        tags:
          - Allele
        parameters:
          - name: q
            in: query
            type: string
            description: JSON filter query
          - name: gp_name
            in: query
            type: string
            description: Genepanel name. Enables the annotation to filter transcripts to only show the relevant ones.
          - name: gp_version
            in: query
            type: string
            description: Genepanel version. Required if gp_name is provided.
          - name: annotation
            in: query
            type: boolean
            description: Whether to include annotation data or not.
          - name: link
            in: query
            type: string
            description: JSON with ids of related entities to load with the alleles
        responses:
          200:
            schema:
              type: array
              items:
                $ref: '#/definitions/Allele'
            description: List of alleles
        """

        order_by = [allele.Allele.chromosome, allele.Allele.start_position]
        alleles, count = self.list_query(
            session, allele.Allele, rest_filter=rest_filter, order_by=order_by
        )

        # Optional extras
        analysis_id = request.args.get("analysis_id")
        gp_name = request.args.get("gp_name")
        gp_version = request.args.get("gp_version")

        genepanel = None
        if gp_name and gp_version:
            genepanel = (
                session.query(gene.Genepanel)
                .filter(gene.Genepanel.name == gp_name, gene.Genepanel.version == gp_version)
                .one()
            )

        adl_kwargs: Dict[str, Any] = {"include_annotation": True, "include_custom_annotation": True}
        if link_filter:
            adl_kwargs["link_filter"] = link_filter
        if analysis_id is not None:
            adl_kwargs["analysis_id"] = int(analysis_id)
        if genepanel:  # TODO: make genepanel required?
            adl_kwargs["genepanel"] = genepanel

        return AlleleDataLoader(session).from_objs(alleles, **adl_kwargs), count


class AlleleGenepanelListResource(LogRequestResource):
    @authenticate()
    @validate_output(GenePanelListResponse)
    def get(self, session: Session, allele_id: int, **kwargs):
        """
        Returns a list of genepanels associated with provided allele_id.
        ---
        summary: List genepanels for one allele
        tags:
          - Allele
        parameters:
          - name: allele_id
            in: path
            type: string
            description: Allele id
        responses:
          200:
            schema:
              type: array
              items:
                $ref: '#/definitions/Genepanel'
            description: List of genepanels
        """
        genepanels = (
            session.query(gene.Genepanel)
            .join(genotype.Genotype.alleles, sample.Sample, sample.Analysis, gene.Genepanel)
            .filter(allele.Allele.id == allele_id)
            .all()
        )

        return schemas.GenepanelSchema(strict=True).dump(genepanels, many=True).data


class AlleleByGeneListResource(LogRequestResource):
    @authenticate()
    @validate_output(AlleleGeneListResponse)
    @rest_filter
    def get(self, session: Session, **kwargs):
        """
        Returns a list of genes, with associated allele ids
        ---
        summary: List genes with allele ids
        tags:
          - Allele
        parameters:
          - name: allele_ids
            in: query
            type: string
            description: Allele ids (comma separated)
        responses:
          200:
            schema:
              type: array
              items:
                $ref: '#/definitions/Genepanel'
            description: List of genes with allele ids
        """

        allele_ids = request.args.get("allele_ids").split(",")

        filters = [
            annotationshadow.AnnotationShadowTranscript.allele_id.in_(
                session.query(func.unnest(cast(allele_ids, ARRAY(Integer)))).subquery()
            )
        ]
        inclusion_regex = config.get("transcripts", {}).get("inclusion_regex")
        if inclusion_regex:
            filters.append(text("transcript ~ :reg").params(reg=inclusion_regex))

        # deduplicate entries
        allele_id_genes = (
            session.query(
                annotationshadow.AnnotationShadowTranscript.symbol,
                annotationshadow.AnnotationShadowTranscript.hgnc_id,
                allele.Allele.id.label("allele_id"),
                allele.Allele.chromosome,
                allele.Allele.start_position,
            )
            .join(allele.Allele)
            .filter(*filters)
            .order_by(
                annotationshadow.AnnotationShadowTranscript.symbol,
                annotationshadow.AnnotationShadowTranscript.hgnc_id,
            )
            .distinct()
            .subquery()
        )
        # aggregate allele_ids by gene, sorted
        allele_id_by_genes = (
            session.query(
                allele_id_genes.c.symbol,
                allele_id_genes.c.hgnc_id,
                func.array_agg(
                    aggregate_order_by(
                        allele_id_genes.c.allele_id,
                        allele_id_genes.c.chromosome.asc(),
                        allele_id_genes.c.start_position.asc(),
                    )
                ).label("allele_ids"),
            )
            .group_by(allele_id_genes.c.symbol, allele_id_genes.c.hgnc_id)
            .all()
        )
        # simulate a "json_agg()" in python as sqlalchemy does not seem to support it :(
        # At least we get an idea how a return type would look like
        return [
            {"symbol": r.symbol, "hgnc_id": r.hgnc_id, "allele_ids": r.allele_ids}
            for r in allele_id_by_genes
        ]


class AlleleAnalysisListResource(LogRequestResource):
    @authenticate()
    @validate_output(AnalysisListResponse)
    @logger(hide_response=False)  # Important! We want to log response for auditing.
    def get(self, session: Session, allele_id: int, **kwargs):
        """
        Returns a list of analyses associated with provided allele_id.
        ---
        summary: List analyses for one allele
        tags:
          - Allele
        parameters:
          - name: allele_id
            in: path
            type: string
            description: Allele id
        responses:
          200:
            schema:
              type: array
              items:
                $ref: '#/definitions/Analysis'
            description: List of analyses
        """
        analyses = (
            session.query(sample.Analysis)
            .join(genotype.Genotype.alleles, sample.Sample, sample.Analysis)
            .filter(allele.Allele.id == allele_id)
            .all()
        )

        aschema = schemas.AnalysisSchema(strict=True)
        return [aschema.dump(a).data for a in analyses]
