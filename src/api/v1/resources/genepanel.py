from sqlalchemy import tuple_
from sqlalchemy.orm import joinedload
from flask import request
from vardb.datamodel import gene

from api.util.util import paginate, rest_filter, authenticate
from api import schemas, ApiError
from api.v1.resource import LogRequestResource


class GenepanelListResource(LogRequestResource):

    @authenticate()
    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, per_page=None, user=None):
        """
        Returns a list of genepanles.

        * Supports `q=` filtering.
        * Supports pagination.
        ---
        summary: List genepanels
        tags:
          - Genepanel
        parameters:
          - name: q
            in: query
            type: string
            description: JSON filter query
        responses:
          200:
            schema:
              type: array
              items:
                $ref: '#/definitions/Genepanel'
            description: List of genepanels
        """
        if rest_filter is None:
            rest_filter = dict()
        rest_filter[("name", "version")] = [(gp.name, gp.version) for gp in user.group.genepanels]

        return self.list_query(
            session,
            gene.Genepanel,
            schema=schemas.GenepanelSchema(),
            rest_filter=rest_filter
        )


class GenepanelResource(LogRequestResource):

    @authenticate()
    def get(self, session, name=None, version=None, user=None):
        """
        Returns a single genepanel.
        ---
        summary: Get genepanel
        tags:
          - Genepanel
        parameters:
          - name: name
            in: path
            type: string
            description: Genepanel name
          - name: version
            in: path
            type: string
            description: Genepanel version
        responses:
          200:
            schema:
                $ref: '#/definitions/Genepanel'
            description: Genepanel object
        """
        if name is None:
            raise ApiError("No genepanel name is provided")
        if version is None:
            raise ApiError("No genepanel version is provided")

        if not session.query(gene.Genepanel.name, gene.Genepanel.version).filter(
            tuple_(gene.Genepanel.name, gene.Genepanel.version) == (name, version)
        ).count():
            raise ApiError("Invalid genepanel name or version")

        transcripts = session.query(
            gene.Gene.hgnc_symbol,
            gene.Gene.hgnc_id,
            gene.Transcript.id,
            gene.Transcript.transcript_name
        ).join(
            gene.Genepanel.transcripts,
            gene.Transcript.gene
        ).filter(
            tuple_(gene.Genepanel.name, gene.Genepanel.version) == (name, version)
        ).order_by(gene.Gene.hgnc_symbol).all()

        phenotypes = session.query(
            gene.Gene.hgnc_symbol,
            gene.Gene.hgnc_id,
            gene.Phenotype.id,
            gene.Phenotype.inheritance
        ).join(
            gene.Phenotype.gene
        ).filter(
            gene.Phenotype.genepanel_name == name,
            gene.Phenotype.genepanel_version == version
        ).order_by(gene.Gene.hgnc_symbol).all()

        genepanel_config = session.query(
            gene.Genepanel.config
        ).filter(
            tuple_(gene.Genepanel.name, gene.Genepanel.version) == (name, version)
        ).scalar()
        genes = {}
        for t in transcripts:
            if t.hgnc_id in genes:
                genes[t.hgnc_id]['transcripts'].append({
                    'id': t.id,
                    'transcript_name': t.transcript_name
                })
            else:
                genes[t.hgnc_id] = {
                    'hgnc_id': t.hgnc_id,
                    'hgnc_symbol': t.hgnc_symbol,
                    'transcripts': [{
                        'id': t.id,
                        'transcript_name': t.transcript_name
                    }],
                    'phenotypes': []
                }

        for p in phenotypes:
            if p.hgnc_id in genes:
                genes[p.hgnc_id]['phenotypes'].append({
                    'id': p.id,
                    'inheritance': p.inheritance
                })

        genes = genes.values()
        genes.sort(key=lambda x: x['hgnc_symbol'])
        for g in genes:
            g['transcripts'].sort(key=lambda x: x['transcript_name'])
            g['phenotypes'].sort(key=lambda x: x['inheritance'])

        result = {
            'name': name,
            'version': version,
            'config': genepanel_config,
            'genes': genes
        }
        return result
