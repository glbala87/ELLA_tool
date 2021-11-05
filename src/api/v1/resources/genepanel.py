from typing import List, Dict, Any
from sqlalchemy import tuple_, func, literal, and_, desc, Float
from sqlalchemy.sql import case
from vardb.datamodel import gene, user as user_model
from sqlalchemy import cast
from sqlalchemy.dialects.postgresql import array, ARRAY
from sqlalchemy.types import Integer

from api.util.util import paginate, rest_filter, authenticate, request_json
from api import schemas, ApiError
from api.v1.resource import LogRequestResource
from operator import itemgetter
from itertools import groupby


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
    @request_json(["name", "version", "genes", "usergroups"])
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

        transcript_ids: List[int] = list()
        phenotype_ids: List[int] = list()
        for g in data["genes"]:
            transcript_ids += [t["id"] for t in g["transcripts"]]
            phenotype_ids += [p["id"] for p in g["phenotypes"]]

        transcripts = (
            session.query(gene.Transcript)
            .filter(
                gene.Transcript.id.in_(
                    session.query(
                        func.unnest(cast(array(transcript_ids), ARRAY(Integer)))
                    ).subquery()
                )
            )
            .all()
        )

        phenotypes = (
            session.query(gene.Phenotype)
            .filter(
                gene.Phenotype.id.in_(
                    session.query(
                        func.unnest(cast(array(phenotype_ids), ARRAY(Integer)))
                    ).subquery()
                )
            )
            .all()
        )

        assert len(transcripts) == len(transcript_ids)
        assert len(phenotypes) == len(phenotype_ids)

        genepanel = gene.Genepanel(
            name=data["name"], genome_reference="GRCh37", version=data["version"]
        )
        genepanel.transcripts = transcripts
        genepanel.phenotypes = phenotypes

        allowed_usergroup_ids = (
            session.query(user_model.UserGroupImport.c.usergroupimport_id)
            .filter(user_model.UserGroupImport.c.usergroup_id == user.group.id)
            .scalar_all()
        )

        assert data["usergroups"]
        usergroup_ids = (
            session.query(user_model.UserGroup.id)
            .filter(user_model.UserGroup.name.in_(data["usergroups"]))
            .scalar_all()
        )
        assert len(usergroup_ids) == len(data["usergroups"])

        assert set(usergroup_ids).issubset(allowed_usergroup_ids)

        session.add(genepanel)
        session.flush()

        for ug_id in usergroup_ids:
            session.execute(
                user_model.UserGroupGenepanel.insert().values(
                    usergroup_id=ug_id,
                    genepanel_name=data["name"],
                    genepanel_version=data["version"],
                )
            )

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

        genes: Dict[int, Any] = {}
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

        result_genes: List[Any] = list(genes.values())
        result_genes.sort(key=lambda x: x["hgnc_symbol"])
        for g in result_genes:
            g["transcripts"].sort(key=lambda x: x["transcript_name"])
            g["phenotypes"].sort(key=lambda x: x["inheritance"])

        result = {"name": name, "version": version, "genes": result_genes}
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

        user_genepanels = [(gp.name, gp.version, gp.official) for gp in user.group.genepanels]
        if (name, version) not in user_genepanels:
            raise ApiError("Invalid genepanel name or version")

        # get only official genepanels
        user_genepanels = [gp for gp in user_genepanels if gp.official]
        # get only max version for each genepanel name
        user_genepanels = [
            (k, max(map(itemgetter(1), v)))
            for k, v in groupby(sorted(user_genepanels, key=itemgetter(0)), key=itemgetter(0))
        ]

        genepanel_gene_ids = (
            session.query(gene.Transcript.gene_id, gene.Genepanel.name, gene.Genepanel.version)
            .join(gene.genepanel_transcript)
            .join(gene.Genepanel)
            .filter(tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(user_genepanels))
            .distinct()
        )

        input_genepanel_gene_ids = genepanel_gene_ids.filter(
            gene.Genepanel.name == name, gene.Genepanel.version == version
        ).subquery()

        input_gene_count = session.query(input_genepanel_gene_ids.c.gene_id).distinct().count()

        # Only include official gene panels in comparison
        genepanel_gene_ids = genepanel_gene_ids.filter(gene.Genepanel.official.is_(True)).subquery()

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

        # Missing = total gene count (in our panel) - overlapping
        missing_expr = literal(input_gene_count) - func.count(
            # COUNT only counts non-null, so CASE acts as an filter for the count
            case([(~input_genepanel_gene_ids.c.gene_id.is_(None), True)])
        )
        # Overlap = all gene ids that joined on gene_id
        overlap_expr = func.count(case([(~input_genepanel_gene_ids.c.gene_id.is_(None), True)]))
        # Additional = all gene ids that did not join (i.e. missing in our panel)
        additional_expr = func.count(case([(input_genepanel_gene_ids.c.gene_id.is_(None), True)]))

        # Similarity score:
        # We weigh distance w.r.t. missing + addition count the most, as long as their
        # sum is small compared to panel size.
        # When the distance is large, the overlap similarity kicks in.
        # The following formula has been tested among >50 official panels,
        # on different custom panels and yields good results
        # (keep in mind that missing + addition + overlap are always greater
        # than input count unless the panels are identical):
        #
        # (Overlapping count / input total count) * 2 +
        # input total count / (missing count + addition count)
        #
        stats = (
            session.query(
                genepanel_gene_ids.c.name,
                genepanel_gene_ids.c.version,
                missing_expr.label("missing"),
                overlap_expr.label("overlap"),
                additional_expr.label("additional"),
            )
            .outerjoin(
                input_genepanel_gene_ids,
                and_(input_genepanel_gene_ids.c.gene_id == genepanel_gene_ids.c.gene_id),
            )
            .filter(
                # Exclude input panel from results
                tuple_(genepanel_gene_ids.c.name, genepanel_gene_ids.c.version)
                != (name, version)
            )
            .having(overlap_expr > 0)  # Exclude panels with no overlap
            .order_by(
                desc(
                    (cast(overlap_expr, Float) * 2 / literal(input_gene_count))
                    + (
                        cast(literal(input_gene_count), Float)
                        / (missing_expr + additional_expr + 1)
                    )
                )
            )
            .group_by(genepanel_gene_ids.c.name, genepanel_gene_ids.c.version)
            .limit(5)
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
