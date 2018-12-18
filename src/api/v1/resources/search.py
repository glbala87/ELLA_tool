import re
import json
from flask import request
from sqlalchemy import tuple_, or_, and_, select, text, func
from vardb.datamodel import (
    sample,
    assessment,
    allele,
    gene,
    genotype,
    workflow,
    annotationshadow,
    user as user_model,
)
from api import schemas, ApiError

from api.v1.resource import LogRequestResource
from api.util.alleledataloader import AlleleDataLoader
from api.util.queries import annotation_transcripts_genepanel
from api.util.util import authenticate

from api.config import config


class SearchQuery:

    RE_POSITION_WITH_CHR = re.compile(
        r"^(chr)?((?P<chr>[1-9]{1,2}|[XY]{1}|MT):)(?P<pos1>[0-9]+)(-(?P<pos2>[0-9]+))?$"
    )
    RE_POSITION_WITHOUT_CHR = re.compile(r"^(?P<pos1>[0-9]+)(-(?P<pos2>[0-9]+))?$")
    RE_G_POSITION = re.compile(r"g\.(?P<pos1>[0-9]+)")

    def __init__(self, query):
        self.query_type = None
        self.chr = None
        self.pos1 = None
        self.pos2 = None
        self.username = None
        self.transcript = None
        self.hgnc_id = None
        self.hgvsp = None
        self.hgvsc = None
        self.freetext = None

        self._set_query(query)

    def _match_position(self, freetext):
        matches = dict()
        for expression in [
            SearchQuery.RE_POSITION_WITH_CHR,
            SearchQuery.RE_POSITION_WITHOUT_CHR,
            SearchQuery.RE_G_POSITION,
        ]:
            match = re.search(expression, freetext)
            if match:
                matches.update(match.groupdict())
        return matches

    def _set_query(self, query):

        if query.get("type"):
            self.query_type = query["type"]

        if query.get("user"):
            self.username = query["user"]["username"]
            assert self.username

        if query.get("gene"):
            self.hgnc_id = query["gene"]["hgnc_id"]
            assert self.hgnc_id

        if query.get("freetext"):
            self.freetext = query["freetext"]

            # Try position search first
            matches = self._match_position(self.freetext)
            self.chr = matches.get("chr")
            self.pos1 = matches.get("pos1")
            if self.pos1:
                self.pos1 = int(self.pos1)
            self.pos2 = matches.get("pos2")
            if self.pos2:
                self.pos2 = int(self.pos2)

            # If not match, try HGVS
            if not matches:
                if ":" in self.freetext:
                    self.transcript, hgvs = self.freetext.split(":", 1)
                else:
                    hgvs = self.freetext
                # Use p. first, since HGSVp can include c. in the name
                if "p." in hgvs.lower():
                    self.hgvsp = hgvs
                elif "c." in hgvs.lower():
                    self.hgvsc = hgvs.lower()

    def is_valid_freetext(self):
        return self.freetext and len(self.freetext) > 2 and self.check()

    def is_alleles_search(self):
        return self.query_type == "alleles"

    def is_analyses_search(self):
        return self.query_type == "analyses"

    def is_hgvs(self):
        return bool(self.hgvsc or self.hgvsp)

    def is_position(self):
        return bool(self.pos1)

    def check(self):
        """
        Returns False when search should return no results (user might not be done typing)
        and raises exception when a message is required to user.
        """
        assert self.is_alleles_search() or self.is_analyses_search()

        if self.is_alleles_search():
            if not any([self.hgvsc, self.hgvsp, self.chr, self.pos1, self.username]):
                return False

            if self.hgvsc or self.hgvsp:
                return bool(self.transcript or self.hgnc_id)

            if self.pos2:
                # Require chromosome when range and no negative range
                if not self.chr or self.pos2 < self.pos1:
                    return False
        elif self.is_analyses_search() and not (self.freetext or self.username):
            return False

        return True


class SearchResource(LogRequestResource):

    ANALYSIS_LIMIT = 10
    ALLELE_LIMIT = 10

    # Matches:
    # 14:234234234-123123123
    # chr14:143000-234234
    # 465234-834234
    # 13:123456
    # 123456
    RE_CHR_POS = re.compile(r"^(chr)?((?P<chr>[0-9XYM]*):)?(?P<pos1>[0-9]+)(-(?P<pos2>[0-9]+))?")

    TSQUERY_ESCAPE = ["&", ":", "(", ")", "*", "!", "|"]

    @authenticate()
    def get(self, session, user=None):
        """
        Provides basic search functionality.

        ### Features
        Right now it supports taking in a free text search, which will
        yield matches in one of two categories:
        * Alleles
        * Analysis

        ### Supported queries
        For Alleles and AlleleAssessments supported search queries are:
        * HGVS cDNA name, e.g. c.1312A>G + gene, or NM_00001.2:c.1312A>G
        * HGVS protein name, e.g. p.Ser309PhefsTer6.
        * Genomic positions in the following formats:
          * 123456 (start position)
          * 14:234234234-123123123 (chr, start, end)
          * 13:123456 (chr, start)
          * chr14:143000-234234 (alternate chr format)
          * 465234-834234 (start, end) (in any chromosome)

        For analyses, it will perform a free text search on the name of
        the Analysis.

        ### Limitations

        * ** Search query must be longer than 2 characters. **
        * ** Search results are limited to 10 per category for performance reasons. **

        ---
        summary: Search
        tags:
          - Search
        parameters:
          - name: q
            in: query
            type: string
            description: Search string
        responses:
          200:
            schema:
                type: object
                properties:
                  alleles:
                    type:
                      object
                    properties:
                      name:
                        type: string
                        description: Genepanel name
                      version:
                        type: string
                        description: Genepanel version
                      alleles:
                        type: array
                        items:
                          $ref: '#/definitions/Allele'
                  analysis:
                    $ref: '#/definitions/Analysis'
                  alleleassessments:
                    $ref: '#/definitions/AlleleAssessment'
            description: Search result
        """
        query = request.args.get("q")
        query = json.loads(query)
        search_query = SearchQuery(query)

        matches = {"alleles": [], "analyses": []}

        if not search_query.check():
            return matches
        elif search_query.is_analyses_search():
            # Use all usergroup genepanels
            genepanels = user.group.genepanels
            # Search analysis
            analyses = self._search_analysis(session, search_query, genepanels)
            analysis_ids = [a["id"] for a in analyses]
            analysis_interpretations = self._get_analysis_interpretations(session, analysis_ids)
            for analysis in analyses:
                analysis["interpretations"] = [
                    ai for ai in analysis_interpretations if ai["analysis_id"] == analysis["id"]
                ]
                matches["analyses"].append(analysis)
        elif search_query.is_alleles_search():
            # Use offical usergroup genepanels (unofficial genepanels are subsets of the official genepanels)
            genepanels = [gp for gp in user.group.genepanels if gp.official]
            if search_query.check():
                # Search allele
                alleles = self._search_allele(session, search_query, genepanels)
                allele_ids = [a["id"] for a in alleles]
                allele_interpretations = self._get_allele_interpretations(session, allele_ids)
                for al in alleles:
                    matches["alleles"].append(
                        {
                            "allele": al,
                            "interpretations": [
                                ai for ai in allele_interpretations if ai["allele_id"] == al["id"]
                            ],
                        }
                    )

        return matches

    def _get_analysis_interpretations(self, session, analysis_ids):
        interpretations = (
            session.query(workflow.AnalysisInterpretation)
            .filter(workflow.AnalysisInterpretation.analysis_id.in_(analysis_ids))
            .order_by(workflow.AnalysisInterpretation.date_last_update)
            .all()
        )
        return schemas.AnalysisInterpretationOverviewSchema().dump(interpretations, many=True).data

    def _get_allele_interpretations(self, session, allele_ids):
        interpretations = (
            session.query(workflow.AlleleInterpretation)
            .filter(workflow.AlleleInterpretation.allele_id.in_(allele_ids))
            .order_by(workflow.AlleleInterpretation.date_last_update)
            .all()
        )
        return schemas.AlleleInterpretationOverviewSchema().dump(interpretations, many=True).data

    def _get_analyses_filters(self, session, search_query, genepanels):
        filters = list()

        if not search_query.freetext and not search_query.username:
            return [False]

        # Filter on genepanel(s)
        filters.append(
            tuple_(sample.Analysis.genepanel_name, sample.Analysis.genepanel_version).in_(
                (gp.name, gp.version) for gp in genepanels
            )
        )

        if search_query.freetext:
            re_freetext = re.escape(search_query.freetext)
            # Escape special characters before sending to tsquery
            for t in SearchResource.TSQUERY_ESCAPE:
                re_freetext = re_freetext.replace(t, "\\" + t)
            filters.append(sample.Analysis.name.op("~*")(".*{}.*".format(re_freetext)))

        if search_query.username is not None:
            user_ids = (
                session.query(user_model.User.id)
                .filter(user_model.User.username == search_query.username)
                .subquery()
            )
            filters.extend(
                [
                    sample.Analysis.id == workflow.AnalysisInterpretation.analysis_id,
                    workflow.AnalysisInterpretation.user_id.in_(user_ids),
                ]
            )

        return filters

    def _get_allele_results_ids(self, session, search_query):
        # Use CTEs or else PostgreSQL creates horrible plans

        filters = list()

        if search_query.is_valid_freetext():
            if search_query.is_hgvs():
                hgvs_cte = self._search_allele_hgvs(session, search_query).cte("hgvsc")
                filters.append(allele.Allele.id.in_(select([hgvs_cte.c.allele_id])))
            elif search_query.is_position():
                position_cte = self._search_allele_position(session, search_query)
                if position_cte:
                    position_cte = position_cte.cte("position")
                    filters.append(allele.Allele.id.in_(select([position_cte.c.id])))

        if search_query.username:
            user_id = (
                session.query(user_model.User.id)
                .filter(user_model.User.username == search_query.username)
                .scalar()
            )

            user_cte = (
                session.query(allele.Allele.id)
                .filter(
                    or_(
                        allele.Allele.id.in_(
                            session.query(workflow.AlleleInterpretation.allele_id).filter(
                                workflow.AlleleInterpretation.user_id == user_id
                            )
                        ),
                        allele.Allele.id.in_(
                            session.query(assessment.AlleleAssessment.allele_id).filter(
                                assessment.AlleleAssessment.user_id == user_id
                            )
                        ),
                    )
                )
                .cte("user")
            )
            filters.append(allele.Allele.id.in_(select([user_cte.c.id])))

        allele_ids = session.query(allele.Allele.id)
        if filters:
            allele_ids = allele_ids.filter(*filters)
        else:
            allele_ids = allele_ids.filter(False)
        return allele_ids

    def _search_allele_hgvs(self, session, search_query):
        """
        Performs a search in the database using the
        annotation table to lookup HGVS cDNA (c.) or protein (p.)
        and get the allele_ids for matching annotations.

        :returns: Query of matching allele_ids
        """

        allele_ids = session.query(annotationshadow.AnnotationShadowTranscript.allele_id)
        inclusion_regex = config.get("transcripts", {}).get("inclusion_regex")
        if inclusion_regex:
            allele_ids = allele_ids.filter(text("transcript ~ :reg").params(reg=inclusion_regex))

        if search_query.hgvsp:
            allele_ids = allele_ids.filter(
                func.lower(annotationshadow.AnnotationShadowTranscript.hgvsp).like(
                    search_query.hgvsp.lower() + "%"
                )
            )
        # Our btree indexes are set as "lower(column) text_pattern_ops" and only support rightside wildcard.
        elif search_query.hgvsc:
            allele_ids = allele_ids.filter(
                func.lower(annotationshadow.AnnotationShadowTranscript.hgvsc).like(
                    search_query.hgvsc.lower() + "%"
                )
            )
        else:
            allele_ids = allele_ids.filter(False)

        if search_query.transcript:
            allele_ids = allele_ids.filter(
                # Split out version number, as this might not match VEP annotation
                text("split_part(transcript, '.', 1) = split_part(:transcript, '.', 1)").bindparams(
                    transcript=search_query.transcript
                )
            )

        if search_query.hgnc_id:
            allele_ids = allele_ids.filter(
                annotationshadow.AnnotationShadowTranscript.hgnc_id == search_query.hgnc_id
            )

        return allele_ids

    def _search_allele_position(self, session, search_query):
        # Searches for Alleles within the range provided in query (if any).
        allele_ids = session.query(allele.Allele.id)

        # Searching without chromosome on a region is too heavy
        if search_query.chr is None and search_query.pos2:
            return allele_ids.filter(False)

        if search_query.chr is not None:
            allele_ids = allele_ids.filter(allele.Allele.chromosome == search_query.chr)

        # Specfic location (only pos1)
        if search_query.pos1 is not None and search_query.pos2 is None:
            allele_ids = allele_ids.filter(
                allele.Allele.start_position == search_query.pos1 - 1
            )  # DB is 0-indexed

        # Range (both pos1 and pos2)
        elif search_query.pos1 is not None and search_query.pos2 is not None:
            allele_ids = allele_ids.filter(
                allele.Allele.start_position >= search_query.pos1 - 1,
                allele.Allele.open_end_position <= search_query.pos2,
            )

        return allele_ids

    def _filter_transcripts_query(self, session, alleles, genepanels, search_query):
        """
        Filters the filtered_transcripts in annotation data based on options in search_query.
        """
        allele_ids = [a["id"] for a in alleles]

        if not allele_ids:
            return

        genepanel_transcripts = annotation_transcripts_genepanel(
            session, [(gp.name, gp.version) for gp in genepanels], allele_ids=allele_ids
        ).subquery()

        allele_ids_transcripts = (
            session.query(
                genepanel_transcripts.c.allele_id, genepanel_transcripts.c.annotation_transcript
            )
            .distinct()
            .all()
        )

        def annotation_transcripts_hgvs(transcripts, search_query):
            results = list()
            for t in transcripts:
                if search_query.hgvsc and search_query.hgvsc in t.get("HGVSc", ""):
                    results.append(t)
                if search_query.hgvsp and search_query.hgvsp in t.get("HGVSp", ""):
                    results.append(t)
            return results

        for al in alleles:
            filtered_transcripts = list()

            # Filter transcripts on genepanel
            for transcript in al["annotation"]["transcripts"]:
                if next(
                    (
                        at
                        for at in allele_ids_transcripts
                        if at[0] == al["id"] and at[1] == transcript["transcript"]
                    ),
                    None,
                ):
                    filtered_transcripts.append(transcript)
            if search_query.is_hgvs():
                genepanel_has_hgvs = annotation_transcripts_hgvs(filtered_transcripts, search_query)
                if not genepanel_has_hgvs:
                    filtered_transcripts.extend(
                        annotation_transcripts_hgvs(al["annotation"]["transcripts"], search_query)
                    )
            al["annotation"]["filtered_transcripts"] = sorted(
                list(set([t["transcript"] for t in filtered_transcripts]))
            )

    def _search_allele(self, session, search_query, genepanels):

        # CTE for performance
        allele_results_ids = (
            self._get_allele_results_ids(session, search_query)
            .limit(SearchResource.ALLELE_LIMIT)
            .cte()
        )

        alleles = (
            session.query(allele.Allele)
            .filter(allele.Allele.id.in_(select([allele_results_ids])))
            .order_by(allele.Allele.chromosome, allele.Allele.start_position)
        )
        alleles = alleles.all()

        allele_data = AlleleDataLoader(session).from_objs(
            alleles,
            include_allele_assessment=True,
            analysis_id=None,
            include_allele_report=False,
            include_annotation=True,
            include_reference_assessments=False,
            allele_assessment_schema=schemas.AlleleAssessmentOverviewSchema,
        )

        self._filter_transcripts_query(session, allele_data, genepanels, search_query)
        return allele_data

    def _search_analysis(self, session, query, genepanels):
        analyses = (
            session.query(sample.Analysis)
            .filter(*self._get_analyses_filters(session, query, genepanels))
            .distinct()
            .limit(SearchResource.ANALYSIS_LIMIT)
            .all()
        )
        if analyses:
            aschema = schemas.AnalysisSchema()
            return [aschema.dump(a).data for a in analyses]
        else:
            return []


class SearchOptionsResource(LogRequestResource):

    RESULT_LIMIT = 20

    @authenticate()
    def get(self, session, user=None):

        query = json.loads(request.args["q"])
        result = dict()
        if query.get("gene"):
            gene_results = (
                session.query(gene.Gene.hgnc_symbol, gene.Gene.hgnc_id)
                .join(gene.Transcript, gene.Genepanel.transcripts)
                .filter(
                    # was a bit hard to get the join correct, had to put join condition here
                    gene.Transcript.gene_id == gene.Gene.hgnc_id,
                    tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(
                        [(g.name, g.version) for g in user.group.genepanels]
                    ),
                    # Our btree indexes are set as "lower(column) text_pattern_ops" and only support rightside wildcard.
                    func.lower(gene.Gene.hgnc_symbol).like(query["gene"].lower() + "%"),
                )
                .distinct()
                .order_by(gene.Gene.hgnc_symbol)
                .limit(SearchOptionsResource.RESULT_LIMIT)
            )

            result["gene"] = [{"symbol": r[0], "hgnc_id": r[1]} for r in gene_results.all()]

        if query.get("user"):
            user_results = (
                session.query(
                    user_model.User.username, user_model.User.first_name, user_model.User.last_name
                )
                .filter(
                    user_model.User.username.in_(
                        session.query(user_model.User.username).filter(
                            user_model.User.group_id == user.group_id
                        )
                    ),
                    or_(
                        user_model.User.first_name.ilike(query["user"] + "%"),
                        user_model.User.last_name.ilike(query["user"] + "%"),
                    ),
                )
                .order_by(user_model.User.last_name)
                .limit(SearchOptionsResource.RESULT_LIMIT)
                .all()
            )
            result["user"] = [
                {"username": u[0], "first_name": u[1], "last_name": u[2]} for u in user_results
            ]

        return result
