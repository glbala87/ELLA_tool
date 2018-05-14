import re
import json
from collections import defaultdict
from flask import request
from sqlalchemy import tuple_, or_, and_
from vardb.datamodel import sample, assessment, allele, gene, genotype, workflow, annotationshadow, user as user_model
from api import schemas

from api.v1.resource import LogRequestResource
from api.util.alleledataloader import AlleleDataLoader
from api.util.queries import annotation_transcripts_genepanel
from api.util.util import authenticate, request_json

from api.util.allelefilter import AlleleFilter
from api.config import config


class SearchResource(LogRequestResource):

    ANALYSIS_LIMIT = 10
    ALLELE_LIMIT = 10

    # Matches:
    # 14:234234234-123123123
    # chr14:143000-234234
    # 465234-834234
    # 13:123456
    # 123456
    RE_CHR_POS = re.compile(
        r'^(chr)?((?P<chr>[0-9XYM]*):)?(?P<pos1>[0-9]+)(-(?P<pos2>[0-9]+))?')

    TSQUERY_ESCAPE = ['&', ':', '(', ')', '*', '!', '|']

    @authenticate()
    def get(self, session, user=None):
        """
        Provides basic search functionality.

        ### Features
        Right now it supports taking in a free text search, which will
        yield matches in three categories (potentially at the same time):
        * Alleles
        * AlleleAssessments
        * Analysis

        ### Supported queries
        For Alleles and AlleleAssessments supported search queries are:
        * HGVS cDNA name, e.g. c.1312A>G.
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
        query = request.args.get('q')
        query = json.loads(query)
        filter_alleles = query.get("filter", False)

        matches = dict()

        # Choose which genepanels to filter on. If genepanel is provided in query, use this. Otherwise use usergroup genepanels.
        if query.get("genepanel"):
            query_gp = (query.get('genepanel')[
                        'name'], query.get('genepanel')['version'])
            genepanels = [next(gp for gp in user.group.genepanels if (
                gp.name, gp.version) == query_gp)]
        else:
            genepanels = user.group.genepanels

        # Search analysis
        analyses = self._search_analysis(session, query, genepanels)
        analysis_ids = [a['id'] for a in analyses]
        analysis_interpretations = self._get_analysis_interpretations(
            session, analysis_ids)
        matches['analyses'] = list()
        for analysis in analyses:
            analysis['interpretations'] = [
                ai for ai in analysis_interpretations if ai['analysis_id'] == analysis['id']]
            matches['analyses'].append(analysis)

        # Search allele
        if filter_alleles:
            alleles = self._search_and_filter_alleles(
                session, query, genepanels)
        else:
            alleles = self._search_allele(session, query, genepanels)
        allele_ids = [a['id'] for a in alleles]
        allele_interpretations = self._get_allele_interpretations(
            session, allele_ids)
        matches['alleles'] = list()
        for al in alleles:
            matches['alleles'].append({
                'allele': al,
                'interpretations': [ai for ai in allele_interpretations if ai['allele_id'] == al['id']]
            })
        return matches

    def _get_analysis_interpretations(self, session, analysis_ids):
        interpretations = session.query(workflow.AnalysisInterpretation).filter(
            workflow.AnalysisInterpretation.analysis_id.in_(analysis_ids)
        ).order_by(
            workflow.AnalysisInterpretation.date_last_update
        ).all()
        return schemas.AnalysisInterpretationOverviewSchema().dump(interpretations, many=True).data

    def _get_allele_interpretations(self, session, allele_ids):
        interpretations = session.query(workflow.AlleleInterpretation).filter(
            workflow.AlleleInterpretation.allele_id.in_(allele_ids)
        ).order_by(
            workflow.AlleleInterpretation.date_last_update
        ).all()
        return schemas.AlleleInterpretationOverviewSchema().dump(interpretations, many=True).data

    def _get_analyses_filters(self, session, query, genepanels):
        filters = list()

        q_freetext = query.get("freetext")
        if q_freetext:
            q_freetext = re.escape(q_freetext)
        q_gene = query.get("gene")
        q_user = query.get("user")
        # The query for genepanel is already applied to genepanels

        if q_freetext is not None and q_freetext != "":
            # Escape special characters before sending to tsquery
            for t in SearchResource.TSQUERY_ESCAPE:
                q_freetext = q_freetext.replace(t, '\\' + t)
            filters.append(sample.Analysis.name.op(
                '~*')('.*{}.*'.format(q_freetext)))

        if q_gene is not None:
            allele_ids_in_gene = self._search_allele_gene(
                session, q_gene['hgnc_id'], genepanels)
            filters.extend([
                sample.Analysis.id == genotype.Genotype.analysis_id,
                or_(
                    genotype.Genotype.allele_id.in_(allele_ids_in_gene),
                    genotype.Genotype.secondallele_id.in_(
                        allele_ids_in_gene)
                )
            ])

        # Filter on genepanel(s)
        filters.append(tuple_(sample.Analysis.genepanel_name, sample.Analysis.genepanel_version).in_(
            (gp.name, gp.version) for gp in genepanels))

        if q_user is not None:
            user_ids = session.query(user_model.User.id).filter(
                user_model.User.username == q_user['username']).subquery()
            filters.extend([
                sample.Analysis.id == workflow.AnalysisInterpretation.analysis_id,
                workflow.AnalysisInterpretation.user_id.in_(user_ids)
            ])

        return filters

    def _get_alleles_filters(self, session, query, genepanels):
        filters = list()

        q_freetext = query.get("freetext")
        q_gene = query.get("gene")
        q_user = query.get("user")
        # The query for genepanel is already applied to genepanels

        if q_freetext is not None and q_freetext != "":
            allele_ids = self._search_allele_freetext(
                session, q_freetext, genepanels)
            filters.append(allele.Allele.id.in_(allele_ids))

        if q_gene is not None:
            allele_ids_in_gene = self._search_allele_gene(
                session, q_gene['hgnc_id'], genepanels)
            filters.append(allele.Allele.id.in_(allele_ids_in_gene))

        allele_ids_in_genepanels = self._search_allele_genepanels(
            session, genepanels)
        filters.append(allele.Allele.id.in_(allele_ids_in_genepanels))

        if q_user is not None:
            user_ids = session.query(user_model.User.id).filter(
                user_model.User.username == q_user['username']).subquery()
            filters.append(or_(
                and_(
                    workflow.AlleleInterpretation.user_id.in_(user_ids),
                    workflow.AlleleInterpretation.allele_id == allele.Allele.id
                ),
                and_(
                    assessment.AlleleAssessment.user_id.in_(user_ids),
                    assessment.AlleleAssessment.allele_id == allele.Allele.id
                )
            ))

        return filters

    def _get_chr_pos(self, query):
        """
        Parses a query string for data that describes a genomic
        position.
        """
        matches = re.search(SearchResource.RE_CHR_POS, query)
        if matches:
            data = matches.groupdict()
            new_data = {
                'chr': data['chr'],
                'pos1': None,
                'pos2': None
            }
            try:
                if data.get('pos1'):
                    # Database is 0-indexed
                    new_data['pos1'] = int(data['pos1']) - 1
                if data.get('pos2'):
                    new_data['pos2'] = int(data['pos2'])
            except ValueError:
                pass

            return new_data

    def _search_allele_hgvs(self, session, freetext, genepanels):
        """
        Performs a search in the database using the
        annotation table to lookup HGVS cDNA (c.) or protein (p.)
        and get the allele_ids for matching annotations.

        :returns: List of allele_ids
        """

        genepanel_transcripts = annotation_transcripts_genepanel(
            session, None, [(gp.name, gp.version) for gp in genepanels]).subquery()
        allele_ids = session.query(
            annotationshadow.AnnotationShadowTranscript.allele_id
        ).filter(
            # Only include transcripts that exists in a genepanel
            annotationshadow.AnnotationShadowTranscript.transcript == genepanel_transcripts.c.annotation_transcript
        )

        # btree indexes only support LIKE statements with no wildcard
        # in the beginning. If we need something else, remember to
        # add/update indexes accordingly
        # Put p. first since some proteins include the c.DNA position
        # e.g. NM_000059.3:c.4068G>A(p.=)
        if 'p.' in freetext:
            allele_ids = allele_ids.filter(
                annotationshadow.AnnotationShadowTranscript.hgvsp.ilike(
                    freetext + "%")
            )
        elif freetext.startswith('c.'):
            allele_ids = allele_ids.filter(
                annotationshadow.AnnotationShadowTranscript.hgvsc.like(
                    freetext + "%")
            )
        else:
            return []

        return allele_ids

    def _search_allele_position(self, session, query):
        # Searches for Alleles within the range provided in query (if any).
        chr_pos = self._get_chr_pos(query)
        if chr_pos:
            allele_ids = session.query(allele.Allele.id)

            if chr_pos['chr'] is not None:
                allele_ids = allele_ids.filter(
                    allele.Allele.chromosome == chr_pos['chr'])

            # Specfic location (only pos1)
            if chr_pos['pos1'] is not None and chr_pos['pos2'] is None:
                allele_ids = allele_ids.filter(
                    allele.Allele.start_position == chr_pos['pos1'])

            # Range (both pos1 and pos2)
            elif chr_pos['pos1'] is not None and chr_pos['pos2'] is not None:
                allele_ids = allele_ids.filter(
                    allele.Allele.start_position >= chr_pos['pos1'],
                    allele.Allele.open_end_position <= chr_pos['pos2'],
                )

            return allele_ids

        return []

    def _search_allele_gene(self, session, gene_hgnc_id, genepanels):
        # Search by transcript symbol
        genepanel_transcripts = annotation_transcripts_genepanel(
            session, None, [(gp.name, gp.version) for gp in genepanels]).subquery()
        result = session.query(
            genepanel_transcripts.c.allele_id,
        ).filter(
            genepanel_transcripts.c.annotation_hgnc_id == gene_hgnc_id,
        ).distinct()

        return result

    def _search_allele_genepanels(self, session, genepanels):
        # Choose wether to filter on genepanel passed in query or genepanels associated with user

        # Filter on genepanels. This is done in two steps:
        # 1. Find alleles in analyses
        # 2. Find alleles imported without analyses, but with an allele interpretation
        allele_ids_analyses_in_genepanels = session.query(
            allele.Allele.id
        ).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis,
            gene.Genepanel,
        )

        allele_ids_workflow_in_genepanels = session.query(
            allele.Allele.id
        ).join(
            workflow.AlleleInterpretation
        )

        allele_ids_analyses_in_genepanels = allele_ids_analyses_in_genepanels.filter(
            tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(
                (gp.name, gp.version) for gp in genepanels)
        ).distinct()

        allele_ids_workflow_in_genepanels = allele_ids_workflow_in_genepanels.filter(
            tuple_(workflow.AlleleInterpretation.genepanel_name, workflow.AlleleInterpretation.genepanel_version).in_(
                (gp.name, gp.version) for gp in genepanels)
        ).distinct()

        allele_ids_in_genepanels = allele_ids_analyses_in_genepanels.union(
            allele_ids_workflow_in_genepanels).distinct()

        return allele_ids_in_genepanels

    def _search_allele_freetext(self, session, freetext, genepanels):
        """
        Search for alleles for the given input.
        Try first a search on HGVS cDNA and protein,
        if not matches, try a position search.
        Idea is that user either searched by a HGVS name or
        by using the genomic position.
        """

        allele_ids = self._search_allele_hgvs(session, freetext, genepanels)

        if not allele_ids:
            allele_ids = self._search_allele_position(session, freetext)

        return allele_ids

    def _get_genepanel_allele_ids(self, session, allele_ids, genepanels):
        # Get genepanels for the alleles
        all_allele_ids = session.query(
            gene.Genepanel.name,
            gene.Genepanel.version,
            allele.Allele.id
        )

        genepanel_analyses_allele_ids = all_allele_ids.join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis,
            gene.Genepanel
        ).filter(
            allele.Allele.id.in_(allele_ids),
            tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(
                (gp.name, gp.version) for gp in genepanels),
        ).distinct()

        genepanel_workflow_allele_ids = all_allele_ids.join(
            workflow.AlleleInterpretation
        ).filter(
            allele.Allele.id.in_(allele_ids),
            tuple_(workflow.AlleleInterpretation.genepanel_name, workflow.AlleleInterpretation.genepanel_version).in_(
                (gp.name, gp.version) for gp in genepanels)
        ).distinct()

        genepanel_allele_ids = genepanel_analyses_allele_ids.union(
            genepanel_workflow_allele_ids)

        return genepanel_allele_ids

    def _filter_transcripts_query(self, session, alleles, genepanels, query):
        allele_ids = [a['id'] for a in alleles]

        genepanel_transcripts = annotation_transcripts_genepanel(
            session,
            allele_ids,
            [(gp.name, gp.version) for gp in genepanels]
        ).subquery()

        allele_ids_transcripts = session.query(
            genepanel_transcripts.c.allele_id,
            genepanel_transcripts.c.annotation_transcript
        ).all()

        freetext = query.get('freetext')
        gene = query.get('gene')
        for al in alleles:
            filtered_transcripts = list()
            for transcript in al['annotation']['transcripts']:
                if next((at for at in allele_ids_transcripts if at[0] == al['id'] and at[1] == transcript['transcript']), None):
                    filtered_transcripts.append(transcript)
            if freetext:
                filtered_transcripts = [t for t in filtered_transcripts if freetext in t.get(
                    'HGVSc', '') or freetext in t.get('HGVSp', '')]
            if gene:
                filtered_transcripts = [
                    t for t in filtered_transcripts if t['hgnc_id'] == gene['hgnc_id']]

            al['annotation']['filtered_transcripts'] = sorted([t['transcript']
                                                               for t in filtered_transcripts])

    def _search_allele(self, session, query, genepanels):
        alleles = session.query(allele.Allele).filter(
            *self._get_alleles_filters(session, query, genepanels)
        ).distinct().limit(SearchResource.ALLELE_LIMIT).all()

        allele_data = AlleleDataLoader(session).from_objs(
            alleles,
            include_allele_assessment=True,
            include_genotype_samples=False,
            include_allele_report=False,
            include_annotation=True,
            include_reference_assessments=False,
            allele_assessment_schema=schemas.AlleleAssessmentOverviewSchema
        )
        self._filter_transcripts_query(session, allele_data, genepanels, query)
        return allele_data

    def _search_and_filter_alleles(self, session, query, genepanels):
        allele_ids = session.query(allele.Allele.id).filter(
            *self._get_alleles_filters(session, query, genepanels)
        )

        genepanel_allele_ids = self._get_genepanel_allele_ids(
            session, allele_ids, genepanels)

        # Filter alleles. Filter alleles in batches, to avoid filtering huge amount of allele ids
        # We want to stop filtering when we reach SearchResource.ALLELE_LIMIT
        gp_allele_ids = defaultdict(list)
        gp_nonfiltered_alleles = defaultdict(list)
        N = 10 * SearchResource.ALLELE_LIMIT  # Number of variants to filter each batch

        af = AlleleFilter(session, config)

        def filter_alleles(gp_allele_ids):
            filtered_alleles = af.filter_alleles(gp_allele_ids)
            return filtered_alleles

        def update_non_filtered(gp_allele_ids, gp_nonfiltered_alleles):
            gp_nonfiltered_slice = filter_alleles(gp_allele_ids)
            for k in gp_nonfiltered_slice:
                gp_nonfiltered_alleles[k].extend(
                    gp_nonfiltered_slice[k]["allele_ids"])

        for i, (gp_name, gp_version, allele_id) in enumerate(genepanel_allele_ids):
            gp_allele_ids[(gp_name, gp_version)].append(allele_id)

            if i > 0 and i % N == 0:
                # Filter batch
                update_non_filtered(gp_allele_ids, gp_nonfiltered_alleles)

                # Reset gp_allele_ids, so we do not filter variants twice
                gp_allele_ids = defaultdict(list)

                num_variants = sum(len(v)
                                   for v in gp_nonfiltered_alleles.values())
                if num_variants >= SearchResource.ALLELE_LIMIT:
                    break

        # If there are still gp_allele ids in data it means that we did not hit ALLELE_LIMIT.
        if len(gp_allele_ids):
            update_non_filtered(gp_allele_ids, gp_nonfiltered_alleles)

        # Load allele data for filtered variants
        all_allele_ids = sum([v for v in gp_nonfiltered_alleles.values()], [])
        all_alleles = session.query(allele.Allele).filter(allele.Allele.id.in_(
            all_allele_ids)).limit(SearchResource.ALLELE_LIMIT).all()

        allele_data = AlleleDataLoader(session).from_objs(
            all_alleles,
            include_allele_assessment=True,
            include_genotype_samples=False,
            include_allele_report=False,
            include_annotation=True,
            include_reference_assessments=False
        )

        self._filter_transcripts_query(session, allele_data, genepanels, query)
        return allele_data

    def _search_analysis(self, session, query, genepanels):
        analyses = session.query(sample.Analysis).filter(
            *self._get_analyses_filters(session, query, genepanels)
        ).distinct().limit(SearchResource.ANALYSIS_LIMIT).all()
        if analyses:
            return schemas.AnalysisSchema().dump(analyses, many=True).data
        else:
            return []


class SearchOptionsResource(LogRequestResource):

    RESULT_LIMIT = 20

    @authenticate()
    def get(self, session, user=None):

        query = json.loads(request.args['q'])
        result = dict()
        if 'gene' in query:
            genepanel_hgnc_ids = session.query(gene.Gene.hgnc_id).join(
                gene.Transcript,
                gene.Genepanel.transcripts
            ).filter(
                # was a bit hard to get the join correct, had to put join condition here
                gene.Transcript.gene_id == gene.Gene.hgnc_id,
                tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(
                    [(g.name, g.version) for g in user.group.genepanels])
            ).distinct()

            gene_results = session.query(
                annotationshadow.AnnotationShadowTranscript.symbol,
                annotationshadow.AnnotationShadowTranscript.hgnc_id
            ).filter(
                annotationshadow.AnnotationShadowTranscript.symbol.ilike(
                    query['gene'] + '%'),
                annotationshadow.AnnotationShadowTranscript.hgnc_id.in_(
                    genepanel_hgnc_ids),
            ).distinct().order_by(
                annotationshadow.AnnotationShadowTranscript.symbol
            ).limit(SearchOptionsResource.RESULT_LIMIT)

            result['gene'] = [{'symbol': r[0], 'hgnc_id': r[1]}
                              for r in gene_results.all()]

        if 'genepanel' in query:
            genepanel_results = session.query(
                gene.Genepanel.name,
                gene.Genepanel.version
            ).filter(
                or_(
                    gene.Genepanel.name.ilike(query['genepanel'] + '%'),
                    gene.Genepanel.version.ilike(query['genepanel'] + '%')
                ),
                tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(
                    [(g.name, g.version) for g in user.group.genepanels])
            ).limit(SearchOptionsResource.RESULT_LIMIT).all()
            result['genepanel'] = [{'name': g[0], 'version': g[1]}
                                   for g in genepanel_results]

        if 'user' in query:
            user_results = session.query(
                user_model.User.username,
                user_model.User.first_name,
                user_model.User.last_name
            ).filter(
                user_model.User.username.in_(
                    session.query(user_model.User.username).filter(
                        user_model.User.group_id == user.group_id)
                ),
                or_(
                    user_model.User.first_name.ilike(query['user'] + '%'),
                    user_model.User.last_name.ilike(query['user'] + '%')
                )
            ).order_by(user_model.User.last_name).limit(SearchOptionsResource.RESULT_LIMIT).all()
            result['user'] = [
                {'username': u[0], 'first_name': u[1], 'last_name': u[2]} for u in user_results]

        return result
