import re
import json
from collections import defaultdict
from flask import request
from sqlalchemy import tuple_, or_, and_
from sqlalchemy.sql import text
from vardb.datamodel import sample, assessment, allele, gene, genotype, workflow, user

from api import schemas

from api.v1.resource import LogRequestResource
from api.util.alleledataloader import AlleleDataLoader

from api.util.annotationprocessor.annotationprocessor import TranscriptAnnotation
from api.util.util import authenticate

from api.util.allelefilter import AlleleFilter
from api.config import config

class SearchResource(LogRequestResource):


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
        * HGVS cDNA name, e.g. c.1312A>G (case insensitive) or NM_000059:c.920_921insT or
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
        query = json.loads(query)
        filter_alleles = query.get("filter", False)

        matches = dict()
        genepanels = user.group.genepanels

        # Search analysis
        matches['analyses'] = self._search_analysis(session, query, genepanels)

        # Search allele
        if filter_alleles:
            matches["alleles"] = self._search_and_filter_alleles(session, query, genepanels)
        else:
            matches["alleles"] = self._search_allele(session, query, genepanels)


        for item in matches["alleles"]:
            print item["name"], item["version"], len(item["alleles"])
        #matches['alleles'] = self._alleles_by_genepanel(session, allele_ids, genepanels)
        return matches


    def _get_analyses_filters(self, session, query, genepanels):
        filters = list()

        freetext = query.get("freetext")
        gene = query.get("gene")
        genepanel = query.get("genepanel")
        user = query.get("user")

        if freetext is not None and freetext != "":
            # Escape special characters before sending to tsquery
            for t in SearchResource.TSQUERY_ESCAPE:
                freetext = freetext.replace(t, '\\' + t)
            filters.append(sample.Analysis.name.op('~*')('.*{}.*'.format(freetext)))

        if gene is not None:
            allele_ids_in_gene = self._search_allele_gene(session, gene)
            filters.extend([
                sample.Analysis.id == genotype.Genotype.analysis_id,
                or_(
                    genotype.Genotype.allele_id.in_(allele_ids_in_gene),
                    genotype.Genotype.secondallele_id.in_(allele_ids_in_gene)
                )
                ]
            )

        if genepanel is not None:
            genepanel_name = genepanel[0]
            genepanel_version = genepanel[1]
            filters.append(
                tuple_(sample.Analysis.genepanel_name, sample.Analysis.genepanel_version) == (genepanel_name, genepanel_version)
            )
        else:
            filters.append(tuple_(sample.Analysis.genepanel_name, sample.Analysis.genepanel_version).in_((gp.name, gp.version) for gp in genepanels))

        if user is not None:
            filters.extend([
                sample.Analysis.id == workflow.AnalysisInterpretation.analysis_id,
                workflow.AnalysisInterpretation.user_id == user
            ])

        return filters

    def _get_alleles_filters(self, session, query, genepanels):
        filters = list()

        q_freetext = query.get("freetext")
        q_gene = query.get("gene")
        q_genepanel = query.get("genepanel")
        q_user = query.get("user")

        if q_freetext is not None and q_freetext != "":
            allele_ids = self._search_allele_freetext(session, q_freetext)
            filters.append(allele.Allele.id.in_(allele_ids))

        if q_gene is not None:
            allele_ids_in_gene = self._search_allele_gene(session, q_gene)
            filters.append(allele.Allele.id.in_(allele_ids_in_gene))

        # Filter on genepanels. This is done either with genepanels passed as parameter, or genepanel in query
        allele_ids_in_genepanels = session.query(
            allele.Allele.id
        ).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis,
            gene.Genepanel
        )
        if q_genepanel is not None:
            genepanel_name = q_genepanel[0]
            genepanel_version = q_genepanel[1]
            allele_ids_in_genepanels = allele_ids_in_genepanels.filter(
                genotype.Genotype.sample_id == sample.Sample.id,
                tuple_(gene.Genepanel.name, gene.Genepanel.version) == (genepanel_name, genepanel_version)
            ).distinct()

            allele_ids = [a[0] for a in allele_ids_in_genepanels]

            filters.append(allele.Allele.id.in_(allele_ids))
        else:
            allele_ids_in_genepanels = allele_ids_in_genepanels.filter(
                genotype.Genotype.sample_id == sample.Sample.id,
                tuple_(gene.Genepanel.name, gene.Genepanel.version).in_((gp.name, gp.version) for gp in genepanels),
            ).all()

            allele_ids = [a[0] for a in allele_ids_in_genepanels]

            filters.append(allele.Allele.id.in_(allele_ids))

        if q_user is not None:
            filters.append(or_(
                and_(
                    workflow.AlleleInterpretation.user_id == q_user,
                    workflow.AlleleInterpretation.allele_id == allele.Allele.id
                ),
                and_(
                    assessment.AlleleAssessment.user_id == q_user,
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
                    new_data['pos1'] = int(data['pos1']) - 1  # Database is 0-indexed
                if data.get('pos2'):
                    new_data['pos2'] = int(data['pos2'])
            except ValueError:
                pass

            return new_data

    def _search_allele_hgvs(self, session, freetext):
        """
        Performs a search in the database using the
        annotation table to lookup HGVS cDNA or protein
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
        if 'p.' in freetext:
            where_clause = "transcript_list->>'HGVSp' ~* :query"
        elif 'c.' in freetext:
            where_clause = "transcript_list->>'HGVSc' ~* :query"

        if where_clause:
            allele_query = text(allele_query.format(where_clause=where_clause))
            # Use session.execute() and bind parameters to avoid injection risk.
            # If you considered changing this to Python's format() function,
            # please stop coding and take a course on SQL injections.
            result = session.execute(allele_query, {'query': '.*'+freetext+'.*'})
            allele_ids = [r[0] for r in result]
            return allele_ids
        return []

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

        return []

    def _search_allele_gene(self, session, gene):
        # Search by transcript symbol
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

        where_clause = "transcript_list->>'symbol' = :query"

        if where_clause:
            allele_query = text(allele_query.format(where_clause=where_clause))
            # Use session.execute() and bind parameters to avoid injection risk.
            # If you considered changing this to Python's format() function,
            # please stop coding and take a course on SQL injections.
            result = session.execute(allele_query, {'query': gene })
            allele_ids = [r[0] for r in result]
            return allele_ids
        return []

    def _search_allele_freetext(self, session, freetext):
        """
        Search for alleles for the given input.
        Try first a search on HGVS cDNA and protein,
        if not matches, try a position search.
        Idea is that user either searched by a HGVS name or
        by using the genomic position.
        """

        allele_ids = self._search_allele_hgvs(session, freetext)

        if allele_ids == []:
            allele_ids = self._search_allele_position(session, freetext)

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


    def _search_allele(self, session, query, genepanels):
        alleles = session.query(allele.Allele).filter(
            *self._get_alleles_filters(session, query, genepanels)
        ).limit(SearchResource.ALLELE_LIMIT).all()


        allele_data = AlleleDataLoader(session).from_objs(
            alleles,
            include_allele_assessment=True,
            include_genotype_samples=False,
            include_allele_report=False,
            include_annotation=True,
            include_reference_assessments=False
        )

        genepanel_alleles = self._alleles_by_genepanel(session, allele_data, genepanels)

        return genepanel_alleles

    def _search_and_filter_alleles(self, session, query, genepanels):

        if query.get("genepanel") is not None:
            genepanels = [gp for gp in genepanels if (gp.name, gp.version) == tuple(query.get("genepanel"))]

        allele_ids = session.query(allele.Allele.id).filter(
            *self._get_alleles_filters(session, query, genepanels)
        ).all()

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

        gp_allele_ids = defaultdict(list)
        for gp_name, gp_version, allele_id in genepanel_alleles:
            gp_allele_ids[(gp_name, gp_version)].append(allele_id)

        af = AlleleFilter(session, config)
        gp_nonfiltered_alleles = af.filter_alleles(gp_allele_ids)

        all_allele_ids = sum([v["allele_ids"] for v in gp_nonfiltered_alleles.values()], [])
        all_alleles = session.query(allele.Allele).filter(allele.Allele.id.in_(all_allele_ids)).all()

        allele_data = AlleleDataLoader(session).from_objs(
            all_alleles,
            include_allele_assessment=True,
            include_genotype_samples=False,
            include_allele_report=False,
            include_annotation=True,
            include_reference_assessments=False
        )

        alleles_by_genepanel = []
        for (gp_name, gp_version) in gp_nonfiltered_alleles:
            for allele_id in gp_nonfiltered_alleles[(gp_name, gp_version)]["allele_ids"]:
                al = next(ad for ad in allele_data if ad["id"] == allele_id)

                genepanel = next(gp for gp in genepanels if gp.name == gp_name and gp.version == gp_version)

                transcripts = [t['transcript'] for t in al['annotation']['transcripts']]
                al['annotation']['filtered_transcripts'] = TranscriptAnnotation.get_genepanel_transcripts(
                    transcripts,
                    genepanel
                )

                item = next((a for a in alleles_by_genepanel if a['name'] == gp_name and a['version'] == gp_version), None)
                if item is None:
                    item = {
                        'name': gp_name,
                        'version': gp_version,
                        'alleles': list()
                    }
                    alleles_by_genepanel.append(item)
                item["alleles"].append(al)

        return alleles_by_genepanel


    def _search_analysis(self, session, query, genepanels):
            analyses = session.query(sample.Analysis).filter(
                *self._get_analyses_filters(session, query, genepanels)
            ).limit(SearchResource.ANALYSIS_LIMIT).all()
            if analyses:
                return schemas.AnalysisFullSchema().dump(analyses, many=True).data
            else:
                return []

if __name__ == "__main__":
    import json
    from vardb.datamodel import DB
    db = DB()
    db.connect()

    session = db.session

    u = session.query(
        user.User
    ).filter(
        user.User.id == 5,
    ).one()
    print u.group.genepanels

    s = SearchResource()
    r = s._search_allele(session, {
                                #"freetext": "13:32890646",
                                #"gene": "CACNB4",
                                "genepanel": ["Ciliopati", "v05"],
                                #"user": 1,
                            }, u.group.genepanels
    )

    for _r in r:
        print json.dumps(_r, indent=4)
        #print _r.keys()
    print len(r)