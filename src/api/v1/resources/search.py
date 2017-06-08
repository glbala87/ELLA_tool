import re
from flask import request
from sqlalchemy import tuple_
from sqlalchemy.sql import text
from vardb.datamodel import sample, assessment, allele, gene, genotype

from api import schemas

from api.v1.resource import Resource
from api.util.alleledataloader import AlleleDataLoader

from api.util.annotationprocessor.annotationprocessor import TranscriptAnnotation
from api.util.util import authenticate

class SearchResource(Resource):


    ANALYSIS_LIMIT = 10
    ALLELE_LIMIT = 10
    ALLELE_ASSESSMENT_LIMIT = 10

    # Matches:
    # 14:234234234-123123123
    # chr14:143000-234234
    # 465234-834234
    # 13:123456
    # 123456
    RE_CHR_POS = re.compile(r'^(chr)?((?P<chr>[0-9XYM]*):)?(?P<pos1>[0-9]+)(-(?P<pos2>[0-9]+))?')

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
        * HGVS c.DNA name, e.g. c.1312A>G (case insensitive) or NM_000059:c.920_921insT or
          just NM_000059.
        * HGVS protein name, e.g. p.Ser309PhefsTer6 or NP_000050.2:p.Ser309PhefsTer6
          or just NP_000050.
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
        if not query or (query and len(query) < 3):
            return {}

        matches = dict()
        genepanels = user.group.genepanels

        # Search analysis
        matches['analyses'] = self._search_analysis(session, query, genepanels)

        # Search alleles with assessments
        alleles_with_assessment = self._search_alleleassessment(session, query)
        matches['alleleassessments'] = self._alleles_by_genepanel(session, alleles_with_assessment, genepanels)

        # Search alleles without assessments
        alleles_without_assessment = self._search_allele(session, query, skip=[a["id"] for a in alleles_with_assessment])
        matches['alleles'] = self._alleles_by_genepanel(session, alleles_without_assessment, genepanels)

        return matches

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
                    new_data['pos1'] = int(data['pos1']) - 1  # Database is 0-indexed
                if data.get('pos2'):
                    new_data['pos2'] = int(data['pos2'])
            except ValueError:
                pass

            return new_data

    def _search_allele_hgvs(self, session, query):
        """
        Performs a search in the database using the
        annotation table to lookup HGVS c.DNA or protein
        and get the allele_ids for matching annotations.

        For performance reasons there's a hardcoded
        (but generous) limit of 5000 allele_ids to avoid
        dumping the whole database for general matches.

        This is needed since we're filtering on indirect objects
        later (like AlleleAssessments) and we don't want
        to miss any hits.
        The final number of results should be limited further
        downstream.

        :returns: List of allele_ids
        """
        allele_ids = list()

        # Search by c.DNA and p. names
        # Query unwraps 'CSQ' JSON array as intermediate
        # table then searches that table for a match.
        allele_query = """with annotation_transcripts as (
            SELECT
               a.allele_id,
               jsonb_array_elements(a.annotations->'transcripts') AS transcript_list
            FROM annotation as a
        )
        SELECT DISTINCT allele_id FROM annotation_transcripts
        WHERE {where_clause} LIMIT 5000
        """

        where_clause = ''
        # Put p. first since some proteins include the c.DNA position
        # e.g. NM_000059.3:c.4068G>A(p.=)
        if 'p.' in query:
            where_clause = "transcript_list->>'HGVSp' ~* :query"
        elif 'c.' in query:
            where_clause = "transcript_list->>'HGVSc' ~* :query"

        if where_clause:
            allele_query = text(allele_query.format(where_clause=where_clause))
            # Use session.execute() and bind parameters to avoid injection risk.
            # If you considered changing this to Python's format() function,
            # please stop coding and take a course on SQL injections.
            result = session.execute(allele_query, {'query': '.*'+query+'.*'})
            allele_ids = [r[0] for r in result]
            return allele_ids
        return None

    def _search_allele_position(self, session, query):
        # Searches for Alleles within the range provided in query (if any).
        chr_pos = self._get_chr_pos(query)
        if chr_pos:
            qallele = session.query(allele.Allele.id)

            if chr_pos['chr'] is not None:
                qallele = qallele.filter(allele.Allele.chromosome == chr_pos['chr'])

            # Specfic location (only pos1)
            if chr_pos['pos1'] is not None and chr_pos['pos2'] is None:
                qallele = qallele.filter(allele.Allele.start_position == chr_pos['pos1'])

            # Range (both pos1 and pos2)
            elif chr_pos['pos1'] is not None and chr_pos['pos2'] is not None:
                qallele = qallele.filter(
                    allele.Allele.start_position >= chr_pos['pos1'],
                    allele.Allele.open_end_position <= chr_pos['pos2'],
                )

            result = qallele.limit(SearchResource.ALLELE_LIMIT).all()
            allele_ids = [r[0] for r in result]
            return allele_ids

        return None

    def _search_allele_ids(self, session, query):
        """
        Search for alleles for the given input.
        Try first a search on HGVS c.DNA and protein,
        if not matches, try a position search.
        Idea is that user either searched by a HGVS name or
        by using the genomic position.
        """

        allele_ids = self._search_allele_hgvs(session, query)

        if allele_ids is None:
            allele_ids = self._search_allele_position(session, query)

        return allele_ids

    def _alleles_by_genepanel(self, session, alleles, genepanels):
        """
        Structures the alleles according the the genepanel(s)
        they belong to, and filters the transcripts
        (sets allele.annotation.filtered to genepanel transcripts)

        Alleles must already be dumped using AlleleDataLoader.
        """
        allele_ids = [a['id'] for a in alleles]

        # Get genepanels for the alleles
        genepanel_alleles = session.query(
            gene.Genepanel.name,
            gene.Genepanel.version,
            allele.Allele.id
        ).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis,
            gene.Genepanel
        ).filter(
            tuple_(gene.Genepanel.name, gene.Genepanel.version).in_((gp.name, gp.version) for gp in genepanels),
            genotype.Genotype.sample_id == sample.Sample.id,
            allele.Allele.id.in_(allele_ids)
        ).distinct().all()

        # Iterate, filter transcripts and add to final data
        alleles_by_genepanel = list()
        for gp_name, gp_version, allele_id in genepanel_alleles:
            al = next(a for a in alleles if a['id'] == allele_id)
            genepanel = next(gp for gp in genepanels if gp.name == gp_name and gp.version == gp_version)

            transcripts = [t['transcript'] for t in al['annotation']['transcripts']]
            al['annotation']['filtered_transcripts'] = TranscriptAnnotation.get_genepanel_transcripts(
                transcripts,
                genepanel
            )

            # Add allele to genepanel -> allele list
            item = next((a for a in alleles_by_genepanel if a['name'] == gp_name and a['version'] == gp_version), None)
            if item is None:
                item = {
                    'name': gp_name,
                    'version': gp_version,
                    'alleles': list()
                }
                alleles_by_genepanel.append(item)

            item['alleles'].append(al)

        return alleles_by_genepanel

    def _search_allele(self, session, query, skip=None):
        allele_ids = self._search_allele_ids(session, query)
        if skip is not None:
            allele_ids = list(set(allele_ids)-set(skip))

        if allele_ids:
            alleles = session.query(allele.Allele).filter(
                allele.Allele.id.in_(allele_ids)
            ).limit(SearchResource.ALLELE_LIMIT).all()
            return AlleleDataLoader(session).from_objs(
                alleles,
                include_allele_assessment=False,
                include_reference_assessments=False
            )
        else:
            return []

    def _search_alleleassessment(self, session, query):
        """
        Searches for Alleles with curated AlleleAssessments matching
        the query.
        """
        allele_ids = self._search_allele_ids(session, query)
        if allele_ids:
            alleles = session.query(allele.Allele).join(assessment.AlleleAssessment).filter(
                allele.Allele.id.in_(allele_ids),
                assessment.AlleleAssessment.allele_id.in_(allele_ids),
                assessment.AlleleAssessment.date_superceeded == None,
            ).limit(SearchResource.ALLELE_LIMIT).all()
            return AlleleDataLoader(session).from_objs(
                alleles,
                include_reference_assessments=False
            )
        return []

    def _search_analysis(self, session, query, genepanels):
        # Escape special characters before sending to tsquery
        for t in SearchResource.TSQUERY_ESCAPE:
            query = query.replace(t, '\\' + t)

        analyses = session.query(sample.Analysis).filter(
            sample.Analysis.name.op('~*')('.*{}.*'.format(query)),
            tuple_(sample.Analysis.genepanel_name, sample.Analysis.genepanel_version).in_((gp.name, gp.version) for gp in genepanels)
        ).limit(SearchResource.ANALYSIS_LIMIT).all()
        if analyses:
            return schemas.AnalysisSchema().dump(analyses, many=True).data
        else:
            return []
