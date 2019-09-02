from sqlalchemy import tuple_, func, literal, and_
from sqlalchemy.sql import label, case
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
                gene.Phenotype.description,
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
                genes[p.hgnc_id]["phenotypes"].append(
                    {"id": p.id, "inheritance": p.inheritance, "description": p.description}
                )

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

        # We calculate results relative to input,
        # i.e. addition_cnt means that a panel given in result has N extra genes
        # compared to input gene panel. Similar for missing, the panel in result is
        # missing N genes present in input panel.

        user_genepanels = [(gp.name, gp.version) for gp in user.group.genepanels]
        if (name, version) not in user_genepanels:
            raise ApiError("Invalid genepanel name or version")

        genepanel_gene_ids = (
            session.query(gene.Transcript.gene_id, gene.Genepanel.name, gene.Genepanel.version)
            .join(gene.genepanel_transcript)
            .join(gene.Genepanel)
            .filter(
                tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(user_genepanels),
                gene.Genepanel.official.is_(True),
            )
            .distinct()
        )

        input_genepanel_gene_ids = genepanel_gene_ids.filter(
            gene.Genepanel.name == name, gene.Genepanel.version == version
        ).subquery()

        input_gene_count = session.query(input_genepanel_gene_ids.c.gene_id).distinct().count()

        genepanel_gene_ids = genepanel_gene_ids.subquery()

        # outerjoin example:
        # -------------------------------------------------------------------
        # | name       | version | gene_id | name       | version | gene_id |
        # -------------------------------------------------------------------
        # | Mendeliome | v01     | 8124    | None       | None    | None    |
        # | Ciliopati  | v05     | 4221    | Ciliopati  | v05     | 4221    |
        # | Mendeliome | v01     | 16404   | None       | None    | None    |
        # | Mendeliome | v01     | 966     | Ciliopati  | v05     | 966     |
        # | Mendeliome | v01     | 4887    | None       | None    | None    |
        # input.gene_id is null -> missing from our gene panel
        # input.gene_id is not null -> overlaps our gene panel
        stats = (
            session.query(
                genepanel_gene_ids.c.name,
                genepanel_gene_ids.c.version,
                # COUNT only counts non-null, so CASE acts as an filter for the count
                # Missing = total gene count (in our panel) - overlapping
                label(
                    "missing",
                    literal(input_gene_count)
                    - func.count(case([(~input_genepanel_gene_ids.c.gene_id.is_(None), True)])),
                ),
                # Overlap = all gene ids where that where joined on gene_id
                func.count(case([(~input_genepanel_gene_ids.c.gene_id.is_(None), True)])).label(
                    "overlap"
                ),
                # Additional = all gene ids that did not join (i.e. missing in our panel)
                func.count(case([(input_genepanel_gene_ids.c.gene_id.is_(None), True)])).label(
                    "additional"
                ),
            )
            .outerjoin(
                input_genepanel_gene_ids,
                and_(input_genepanel_gene_ids.c.gene_id == genepanel_gene_ids.c.gene_id),
            )
            .group_by(genepanel_gene_ids.c.name, genepanel_gene_ids.c.version)
        )

        result = {"overlap": []}

        for c in stats:
            result["overlap"].append(
                {
                    "name": c.name,
                    "version": c.version,
                    "addition_cnt": c.additional,
                    "overlap_cnt": c.overlap,
                    "missing_cnt": c.missing,
                }
            )
        return result
