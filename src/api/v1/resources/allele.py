from collections import defaultdict
from flask import request
from sqlalchemy import or_, text
from vardb.datamodel import sample, genotype, allele, gene, annotationshadow

from api import schemas, ApiError
from api.config import config
from api.util.util import rest_filter, link_filter, authenticate, logger, paginate

from datalayer import AlleleDataLoader

from api.v1.resource import LogRequestResource


class AlleleListResource(LogRequestResource):
    @authenticate()
    @paginate
    @link_filter
    @rest_filter
    def get(self, session, rest_filter=None, link_filter=None, user=None, page=None, per_page=None):
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
        annotation = request.args.get("annotation", "true") == "true"

        genepanel = None
        if gp_name and gp_version:
            genepanel = (
                session.query(gene.Genepanel)
                .filter(gene.Genepanel.name == gp_name, gene.Genepanel.version == gp_version)
                .one()
            )

        kwargs = {"include_annotation": False, "include_custom_annotation": False}
        if link_filter:
            kwargs["link_filter"] = link_filter
        if analysis_id is not None:
            kwargs["analysis_id"] = analysis_id
        if genepanel:  # TODO: make genepanel required?
            kwargs["genepanel"] = genepanel
        if annotation:
            kwargs["include_annotation"] = True
            kwargs["include_custom_annotation"] = True
        return AlleleDataLoader(session).from_objs(alleles, **kwargs), count


class AlleleGenepanelListResource(LogRequestResource):
    @authenticate()
    def get(self, session, allele_id, user=None):
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
    @rest_filter
    def get(self, session, rest_filter=None, user=None):
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

        filters = [annotationshadow.AnnotationShadowTranscript.allele_id.in_(allele_ids)]
        inclusion_regex = config.get("transcripts", {}).get("inclusion_regex")
        if inclusion_regex:
            filters.append(text("transcript ~ :reg").params(reg=inclusion_regex))

        allele_id_genes = (
            session.query(
                annotationshadow.AnnotationShadowTranscript.allele_id,
                annotationshadow.AnnotationShadowTranscript.symbol,
                annotationshadow.AnnotationShadowTranscript.hgnc_id,
            )
            .filter(*filters)
            .all()
        )

        pre_sorted_result = defaultdict(set)
        for a in allele_id_genes:
            pre_sorted_result[(a[1], a[2])].add(a[0])

        result = list()
        for key in sorted(
            list(pre_sorted_result.keys()), key=lambda x: x[0] if x[0] is not None else ""
        ):
            allele_ids = pre_sorted_result[key]
            result.append(
                {"symbol": key[0], "hgnc_id": key[1], "allele_ids": sorted(list(allele_ids))}
            )
        return result


class AlleleAnalysisListResource(LogRequestResource):
    @authenticate()
    @logger(hide_response=False)  # Important! We want to log response for auditing.
    def get(self, session, allele_id, user=None):
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
