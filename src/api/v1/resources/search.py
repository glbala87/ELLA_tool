from collections import defaultdict
import re
from flask import request
from sqlalchemy.sql import text
from sqlalchemy.orm import contains_eager
from vardb.datamodel import sample, assessment, allele, gene, genotype

from api import schemas

from api.v1.resource import Resource
from api.util.alleledataloader import AlleleDataLoader

from api.util.annotationprocessor.annotationprocessor import TranscriptAnnotation


class SearchResource(Resource):
    """
    Resource for providing basic search functionality.

    Right now it supports taking in a free text search, which will
    yield matches in three categories (potentially at the same time):
    - Alleles
    - AlleleAssessments
    - Analysis

    For Alleles and AlleleAssessments supported search queries are:
    - HGVS c.DNA name, e.g. c.1312A>G (case insensitive) or NM_000059:c.920_921insT or
      just NM_000059.
    - HGVS protein name, e.g. p.Ser309PhefsTer6 or NP_000050.2:p.Ser309PhefsTer6
      or just NP_000050.
    - Genomic positions in the following formats:
      - 123456  <- start position
      - 14:234234234-123123123 <- chr, start, end
      - 13:123456 <- chr, start
      - chr14:143000-234234 <- alternate chr format
      - 465234-834234 <- start, end (in any chromosome)

    For analyses, it will perform a free text search on the name of
    the Analysis.

    *Search query must be longer than 2 characters.*
    *Search results are limited to 10 per category.*
    """

    ANALYSIS_LIMIT = 10
    ALLELE_LIMIT = 10
    ALLELE_ASSESSMENT_LIMIT = 10

    # Matches:
    # 14:234234234-123123123
    # chr14:143000-234234
    # 465234-834234
    # 13:123456
    # 123456
    RE_CHR_POS = re.compile(r'^(chr)?((?P<chr>[0-9XY]*):)?(?P<pos1>[0-9]+)(-(?P<pos2>[0-9]+))?')

    TSQUERY_ESCAPE = ['&', ':', '(', ')', '*', '!', '|']

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
                    new_data['pos1'] = int(data['pos1'])
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
        allele_query = """with csq_transcripts as (
            SELECT
               a.allele_id,
               jsonb_array_elements(a.annotations->'CSQ') AS csq
            FROM annotation as a
        )
        SELECT DISTINCT allele_id FROM csq_transcripts
        WHERE {where_clause} LIMIT 5000
        """

        where_clause = ''
        # Put p. first since some proteins include the c.DNA position
        # e.g. NM_000059.3:c.4068G>A(p.=)
        if 'p.' in query:
            where_clause = "csq->>'HGVSp' ~* :query"
        elif 'c.' in query:
            where_clause = "csq->>'HGVSc' ~* :query"

        if where_clause:
            allele_query = text(allele_query.format(where_clause=where_clause))
            # Use execute and bind parameters to avoid injection risk.
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
                qallele = qallele.filter(allele.Allele.startPosition == chr_pos['pos1'])

            # Range (both pos1 and pos2)
            elif chr_pos['pos1'] is not None and chr_pos['pos2'] is not None:
                qallele = qallele.filter(
                    allele.Allele.startPosition >= chr_pos['pos1'],
                    allele.Allele.openEndPosition <= chr_pos['pos2'],
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

    def _alleles_by_genepanel(self, session, alleles):
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
            genotype.Genotype.sample_id == sample.Sample.id,
            allele.Allele.id.in_(allele_ids)
        ).all()


        # Load all genepanels
        # TODO: Optimize to load only relevant ones
        genepanels = session.query(gene.Genepanel).all()

        # Iterate, filter transcripts and add to final data
        alleles_by_genepanel = list()
        for gp_name, gp_version, allele_id in genepanel_alleles:
            al = next(a for a in alleles if a['id'] == allele_id)
            genepanel = next(gp for gp in genepanels if gp.name == gp_name and gp.version == gp_version)

            transcripts = [t['Transcript'] for t in al['annotation']['transcripts']]
            al['annotation']['filtered_transcripts'] = TranscriptAnnotation.get_genepanel_transcripts(
                transcripts,
                schemas.GenepanelSchema().dump(genepanel).data
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

    def _search_allele(self, session, query):
        allele_ids = self._search_allele_ids(session, query)

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
        Searches for AlleleAssessments for Alleles matching
        the query.
        """
        allele_ids = self._search_allele_ids(session, query)
        if allele_ids:
            aa = session.query(assessment.AlleleAssessment).join(allele.Allele).filter(
                allele.Allele.id.in_(allele_ids),
                assessment.AlleleAssessment.dateSuperceeded == None,
                assessment.AlleleAssessment.status == 1
            ).limit(SearchResource.ALLELE_ASSESSMENT_LIMIT).all()
            if aa:
                return schemas.AlleleAssessmentSchema().dump(aa, many=True).data
        return []

    def _search_analysis(self, session, query):
        # Escape special characters before sending to tsquery
        for t in SearchResource.TSQUERY_ESCAPE:
            query = query.replace(t, '\\' + t)

        analyses = session.query(sample.Analysis).filter(
            sample.Analysis.name.op('~*')('.*{}.*'.format(query))
        ).limit(SearchResource.ANALYSIS_LIMIT).all()
        if analyses:
            return schemas.AnalysisSchema().dump(analyses, many=True).data
        else:
            return []

    def get(self, session):
        query = request.args.get('q')
        if not query or (query and len(query) < 3):
            return {}

        matches = dict()

        # Search analysis
        matches['analyses'] = self._search_analysis(session, query)

        # Search alleles
        matches['alleles'] = self._alleles_by_genepanel(
            session,
            self._search_allele(session, query)
        )

        # Search alleleassessments
        # TODO: THIS DOESN'T WORK, THERE'S NO ALLELE!
        matches['alleleassessments'] = self._alleles_by_genepanel(
            session,
            self._search_alleleassessment(session, query)
        )

        return matches
