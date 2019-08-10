from sqlalchemy import tuple_, func, literal, and_
from sqlalchemy.sql import label
from sqlalchemy.orm import joinedload, aliased
from flask import request
from vardb.datamodel import gene

from api.util.util import paginate, rest_filter, authenticate, request_json
from api import schemas, ApiError
from api.v1.resource import LogRequestResource


class GenepanelListResource(LogRequestResource):
    @authenticate()
    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, per_page=None, user=None):
        """
        Returns a list of genepanels.

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
        rest_filter["official"] = True

        return self.list_query(
            session,
            gene.Genepanel,
            schema=schemas.GenepanelSchema(),
            rest_filter=rest_filter,
            order_by=["name", "version"],
        )

    @authenticate()
    @request_json(["name", "version", "genes"])
    def post(self, session, data=None, user=None):
        """
        Creates a new genepanel.

        Only supports referencing already existing transcripts and phenotypes.
        ---
        summary: Create genepanel
        tags:
          - Genepanel
        parameters:
          - name: data
            in: body
            required: true
            schema:
              title: Genepanel data
              type: object
              required:
                  - allele_id
                  - evaluation
              properties:
                  name:
                    description: Genepanel name
                    type: string
                  version:
                    description: Genepanel version
                    type: string
                  genes:
                    description: Object with transcripts and phenotypes
                    type: object
            description: Submitted data
        responses:
          200:
            schema:
              type: null
            description: No response
        """
        if not data["name"]:
            raise ApiError("No name given for genepanel")

        if not data["version"]:
            raise ApiError("No version given for genepanel")

        transcript_ids = list()
        phenotype_ids = list()
        for g in data["genes"]:
            transcript_ids += [t["id"] for t in g["transcripts"]]
            phenotype_ids += [p["id"] for p in g["phenotypes"]]

        transcripts = (
            session.query(gene.Transcript).filter(gene.Transcript.id.in_(transcript_ids)).all()
        )

        phenotypes = (
            session.query(gene.Phenotype).filter(gene.Phenotype.id.in_(phenotype_ids)).all()
        )

        assert len(transcripts) == len(transcript_ids)
        assert len(phenotypes) == len(phenotype_ids)

        genepanel = gene.Genepanel(
            name=data["name"], genome_reference="GRCh37", version=data["version"]
        )
        genepanel.transcripts = transcripts
        genepanel.phenotypes = phenotypes

        user.group.genepanels.append(genepanel)

        session.add(genepanel)

        session.commit()
        return None


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

        if (
            not session.query(gene.Genepanel.name, gene.Genepanel.version)
            .filter(tuple_(gene.Genepanel.name, gene.Genepanel.version) == (name, version))
            .count()
        ):
            raise ApiError("Invalid genepanel name or version")

        transcripts = (
            session.query(
                gene.Gene.hgnc_symbol,
                gene.Gene.hgnc_id,
                gene.Transcript.id,
                gene.Transcript.transcript_name,
            )
            .join(gene.Genepanel.transcripts, gene.Transcript.gene)
            .filter(tuple_(gene.Genepanel.name, gene.Genepanel.version) == (name, version))
            .order_by(gene.Gene.hgnc_symbol)
            .all()
        )

        phenotypes = (
            session.query(
                gene.Gene.hgnc_symbol,
                gene.Gene.hgnc_id,
                gene.Phenotype.id,
                gene.Phenotype.inheritance,
            )
            .join(gene.Phenotype.gene)
            .join(gene.genepanel_phenotype)
            .filter(
                gene.genepanel_phenotype.c.genepanel_name == name,
                gene.genepanel_phenotype.c.genepanel_version == version,
            )
            .order_by(gene.Gene.hgnc_symbol)
            .all()
        )

        genes = {}
        for t in transcripts:
            if t.hgnc_id in genes:
                genes[t.hgnc_id]["transcripts"].append(
                    {"id": t.id, "transcript_name": t.transcript_name}
                )
            else:
                genes[t.hgnc_id] = {
                    "hgnc_id": t.hgnc_id,
                    "hgnc_symbol": t.hgnc_symbol,
                    "transcripts": [{"id": t.id, "transcript_name": t.transcript_name}],
                    "phenotypes": [],
                }

        for p in phenotypes:
            if p.hgnc_id in genes:
                genes[p.hgnc_id]["phenotypes"].append({"id": p.id, "inheritance": p.inheritance})

        genes = list(genes.values())
        genes.sort(key=lambda x: x["hgnc_symbol"])
        for g in genes:
            g["transcripts"].sort(key=lambda x: x["transcript_name"])
            g["phenotypes"].sort(key=lambda x: x["inheritance"])

        result = {"name": name, "version": version, "genes": genes}
        return result


class GenepanelStatsResource(LogRequestResource):
    @authenticate()
    def get(self, session, name=None, version=None, user=None):

        if name is None:
            raise ApiError("No genepanel name is provided")
        if version is None:
            raise ApiError("No genepanel version is provided")

        if (
            not session.query(gene.Genepanel.name, gene.Genepanel.version)
            .filter(tuple_(gene.Genepanel.name, gene.Genepanel.version) == (name, version))
            .count()
        ):
            raise ApiError("Invalid genepanel name or version")

        # We calculate results relative to input,
        # i.e. addition_cnt means that a panel given in result has N extra transcripts
        # compared to input gene panel. Similar for missing, the panel in result is
        # missing N transcripts present in input panel.

        base_transcript_ids = session.query(gene.genepanel_transcript.c.transcript_id).filter(
            gene.genepanel_transcript.c.genepanel_name == name,
            gene.genepanel_transcript.c.genepanel_version == version,
        )

        base_transcript_ids_count = base_transcript_ids.count()
        base_transcript_ids = base_transcript_ids.subquery()

        other_addition = (
            session.query(
                gene.genepanel_transcript.c.genepanel_name,
                gene.genepanel_transcript.c.genepanel_version,
                func.count(gene.genepanel_transcript.c.transcript_id).label("addition_cnt"),
            )
            .filter(~gene.genepanel_transcript.c.transcript_id.in_(base_transcript_ids))
            .group_by(
                gene.genepanel_transcript.c.genepanel_name,
                gene.genepanel_transcript.c.genepanel_version,
            )
            .subquery("addition")
        )

        other_overlap = (
            session.query(
                gene.genepanel_transcript.c.genepanel_name,
                gene.genepanel_transcript.c.genepanel_version,
                func.count(gene.genepanel_transcript.c.transcript_id).label("overlap_cnt"),
            )
            .filter(gene.genepanel_transcript.c.transcript_id.in_(base_transcript_ids))
            .group_by(
                gene.genepanel_transcript.c.genepanel_name,
                gene.genepanel_transcript.c.genepanel_version,
            )
            .subquery("overlap")
        )

        other_missing = (
            session.query(
                gene.genepanel_transcript.c.genepanel_name,
                gene.genepanel_transcript.c.genepanel_version,
                label(
                    "missing_cnt",
                    literal(base_transcript_ids_count)
                    - func.count(gene.genepanel_transcript.c.transcript_id),
                ),
            )
            .filter(gene.genepanel_transcript.c.transcript_id.in_(base_transcript_ids))
            .group_by(
                gene.genepanel_transcript.c.genepanel_name,
                gene.genepanel_transcript.c.genepanel_version,
            )
            .subquery("missing")
        )

        # We need to use other_overlap as primary table, using any of the others
        # will exclude the genepanels with either 0 additions or 0 missing.
        # Here we implicitly exclude gene panels with no overlap, but that's what we want

        combined = (
            session.query(
                other_overlap.c.genepanel_name,
                other_overlap.c.genepanel_version,
                func.coalesce(other_addition.c.addition_cnt, 0).label("addition_cnt"),
                other_overlap.c.overlap_cnt,
                func.coalesce(other_missing.c.missing_cnt, 0).label("missing_cnt"),
            )
            .outerjoin(
                other_addition,
                and_(
                    other_overlap.c.genepanel_name == other_addition.c.genepanel_name,
                    other_overlap.c.genepanel_version == other_addition.c.genepanel_version,
                ),
            )
            .outerjoin(
                other_missing,
                and_(
                    other_overlap.c.genepanel_name == other_missing.c.genepanel_name,
                    other_overlap.c.genepanel_version == other_missing.c.genepanel_version,
                ),
            )
            .filter(
                tuple_(other_overlap.c.genepanel_name, other_overlap.c.genepanel_version)
                != (name, version)
            )
            .order_by(  # Put most similar on top
                func.coalesce(other_addition.c.addition_cnt, 0)
                + func.coalesce(other_missing.c.missing_cnt, 0)
            )
            .limit(5)
            .all()
        )

        result = {"overlap": []}

        for c in combined:
            result["overlap"].append(
                {
                    "name": c.genepanel_name,
                    "version": c.genepanel_version,
                    "addition_cnt": c.addition_cnt,
                    "overlap_cnt": c.overlap_cnt,
                    "missing_cnt": c.missing_cnt,
                }
            )
        return result
