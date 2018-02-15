"""
Integration/unit test for the AlleleFilter module.
Since it consists mostly of database queries, it's tested on a live database.
"""
import pytest
import datetime
import pytz
import itertools
from collections import defaultdict
from sqlalchemy import or_, and_

from vardb.datamodel import assessment, workflow, allele, sample, genotype
from api.tests.workflow_helper import WorkflowHelper
from api.tests import interpretation_helper as ih

from api.util.allelefilter import AlleleFilter
from api.config import config


@pytest.fixture
def with_finding_classification():
    return next(o for o in config['classification']['options'] if o.get('include_analysis_with_findings') and o.get('outdated_after_days'))


@pytest.fixture
def without_finding_classification():
    return next(o for o in config['classification']['options'] if not o.get('include_analysis_with_findings') and o.get('outdated_after_days'))


class TestAnalysisOverview(object):

    @pytest.mark.overviewanalysis(order=0)
    def test_prepare_data(self, test_database, session):
        test_database.refresh()  # Reset db

    @pytest.mark.overviewanalysis(order=1)
    def test_initial_state(self, client):

        # Normal endpoint
        r = client.get('/api/v1/overviews/analyses/')

        assert len(r.json['not_started']) == 4
        assert len(r.json['marked_review']) == 0
        assert len(r.json['ongoing']) == 0

        # With-findings
        r = client.get('/api/v1/overviews/analyses/by-findings/')
        assert len(r.json['not_started']) == 4
        assert len(r.json['missing_alleleassessments']) == 4
        assert len(r.json['with_findings']) == 0
        assert len(r.json['without_findings']) == 0
        assert len(r.json['marked_review']) == 0
        assert len(r.json['ongoing']) == 0

        r = client.get('/api/v1/overviews/analyses/')
        assert len(r.json['not_started']) == 4
        assert len(r.json['marked_review']) == 0
        assert len(r.json['ongoing']) == 0

        # Finalized
        r = client.get('/api/v1/overviews/analyses/finalized/')
        assert isinstance(r.json, list) and len(r.json) == 0

    @pytest.mark.overviewanalysis(order=2)
    def test_changes(self, client, session, with_finding_classification, without_finding_classification):

        FIRST_ANALYSIS_ID = 1
        wh = WorkflowHelper('analysis', FIRST_ANALYSIS_ID)

        ##
        # Ongoing
        ##

        interpretation = wh.start_interpretation('testuser1')

        r = client.get('/api/v1/overviews/analyses/by-findings/')

        assert len(r.json['not_started']) == 3
        assert len(r.json['missing_alleleassessments']) == 3
        assert len(r.json['with_findings']) == 0
        assert len(r.json['without_findings']) == 0
        assert len(r.json['marked_review']) == 0
        assert len(r.json['ongoing']) == 1

        assert r.json['ongoing'][0]['id'] == FIRST_ANALYSIS_ID
        assert len(r.json['ongoing'][0]['interpretations']) == 1

        r = client.get('/api/v1/overviews/analyses/')

        assert len(r.json['not_started']) == 3
        assert len(r.json['marked_review']) == 0
        assert len(r.json['ongoing']) == 1

        ##
        # Marked review
        ##

        wh.perform_review_round(interpretation)

        r = client.get('/api/v1/overviews/analyses/by-findings/')

        assert len(r.json['not_started']) == 3
        assert len(r.json['missing_alleleassessments']) == 3
        assert len(r.json['with_findings']) == 0
        assert len(r.json['without_findings']) == 0
        assert len(r.json['marked_review']) == 1
        assert len(r.json['ongoing']) == 0

        assert r.json['marked_review'][0]['id'] == FIRST_ANALYSIS_ID
        assert len(r.json['marked_review'][0]['interpretations']) == 2
        # Check correct sorting on interpretations
        assert r.json['marked_review'][0]['interpretations'][0]['date_last_update'] < r.json['marked_review'][0]['interpretations'][1]['date_last_update']

        r = client.get('/api/v1/overviews/analyses/')

        assert len(r.json['not_started']) == 3
        assert len(r.json['marked_review']) == 1
        assert len(r.json['ongoing']) == 0


        ##
        # Finalize
        ##

        interpretation = wh.start_interpretation('testuser2')
        wh.perform_finalize_round(interpretation)

        r = client.get('/api/v1/overviews/analyses/by-findings/')

        assert len(r.json['not_started']) == 3
        assert len(r.json['missing_alleleassessments']) == 3
        assert len(r.json['with_findings']) == 0
        assert len(r.json['without_findings']) == 0
        assert len(r.json['marked_review']) == 0
        assert len(r.json['ongoing']) == 0

        r = client.get('/api/v1/overviews/analyses/finalized/')
        assert isinstance(r.json, list) and len(r.json) == 1
        assert r.json[0]['id'] == FIRST_ANALYSIS_ID
        interpretations = r.json[0]['interpretations']
        assert interpretations[0]['date_last_update'] < interpretations[1]['date_last_update']
        r = client.get('/api/v1/overviews/analyses/')

        assert len(r.json['not_started']) == 3
        assert len(r.json['marked_review']) == 0
        assert len(r.json['ongoing']) == 0

        ##
        # Test with_findings, non-outdated
        ##

        SECOND_ANALYSIS_ID = 2
        # Create alleleassessments for the alleles in SECOND_ANALYSIS_ID
        interpretation_id = ih.get_interpretation_id_of_last('analysis', SECOND_ANALYSIS_ID)
        interpretation = ih.get_interpretation('analysis', SECOND_ANALYSIS_ID, interpretation_id)
        alleles = ih.get_alleles('analysis', SECOND_ANALYSIS_ID, interpretation['id'], interpretation['allele_ids'])

        # Ensure one with findings, rest without.
        classifications = [with_finding_classification] * 1 + [without_finding_classification] * (len(interpretation['allele_ids']) - 1)
        with_finding_alleleassessment = None
        for allele, classification in zip(alleles, classifications):

            # Supercede the ones with existing classifications
            existing = session.query(assessment.AlleleAssessment).filter(
                assessment.AlleleAssessment.allele_id == allele['id']
            ).one_or_none()

            aa = assessment.AlleleAssessment(
                classification=classification['value'],
                allele_id=allele['id'],
                genepanel_name=interpretation['genepanel_name'],
                genepanel_version=interpretation['genepanel_version'],
                previous_assessment_id=existing.id if existing else None
            )
            session.add(aa)

            if classification == with_finding_classification:
                with_finding_alleleassessment = aa

            if existing:
                existing.date_superceeded = datetime.datetime.now(pytz.utc)

            session.commit()

        assert session.query(assessment.AlleleAssessment).filter(
            assessment.AlleleAssessment.allele_id.in_(interpretation['allele_ids']),
            assessment.AlleleAssessment.date_superceeded.is_(None)
        ).count() == len(interpretation['allele_ids'])

        # Now check overview, one should be in with_findings
        r = client.get('/api/v1/overviews/analyses/by-findings/')
        assert len(r.json['not_started']) == 3
        assert len(r.json['missing_alleleassessments']) == 2
        assert len(r.json['with_findings']) == 1
        assert len(r.json['without_findings']) == 0
        assert len(r.json['marked_review']) == 0
        assert len(r.json['ongoing']) == 0

        r = client.get('/api/v1/overviews/analyses/finalized/')
        assert isinstance(r.json, list) and len(r.json) == 1

        ##
        # Test with_findings, outdated
        ##

        # Make alleleassessment outdated
        org_date_created = with_finding_alleleassessment.date_created
        new_date_created = with_finding_alleleassessment.date_created - datetime.timedelta(days=with_finding_classification['outdated_after_days'] + 1)
        with_finding_alleleassessment.date_created = new_date_created
        session.commit()

        # Now check overview, one should be in with_findings
        r = client.get('/api/v1/overviews/analyses/by-findings/')
        assert len(r.json['not_started']) == 3
        assert len(r.json['missing_alleleassessments']) == 3
        assert len(r.json['with_findings']) == 0
        assert len(r.json['without_findings']) == 0
        assert len(r.json['marked_review']) == 0
        assert len(r.json['ongoing']) == 0

        r = client.get('/api/v1/overviews/analyses/finalized/')
        assert isinstance(r.json, list) and len(r.json) == 1

        # Revert date
        with_finding_alleleassessment.date_created = org_date_created
        session.commit()

        ##
        # Test without_findings, non-outdated
        ##

        # Change classification
        with_finding_alleleassessment.classification = without_finding_classification['value']
        session.commit()

        # Now check overview, one should be in with_findings
        r = client.get('/api/v1/overviews/analyses/by-findings/')
        assert len(r.json['not_started']) == 3
        assert len(r.json['missing_alleleassessments']) == 2
        assert len(r.json['with_findings']) == 0
        assert len(r.json['without_findings']) == 1
        assert len(r.json['marked_review']) == 0
        assert len(r.json['ongoing']) == 0

        r = client.get('/api/v1/overviews/analyses/finalized/')
        assert isinstance(r.json, list) and len(r.json) == 1

        ##
        # Test without_findings, outdated
        ##

        # Change classification
        org_date_created = with_finding_alleleassessment.date_created
        new_date_created = with_finding_alleleassessment.date_created - datetime.timedelta(days=without_finding_classification['outdated_after_days'] + 1)
        with_finding_alleleassessment.date_created = new_date_created
        session.commit()

        # Now check overview, one should be in with_findings
        r = client.get('/api/v1/overviews/analyses/by-findings/')
        assert len(r.json['not_started']) == 3
        assert len(r.json['missing_alleleassessments']) == 3
        assert len(r.json['with_findings']) == 0
        assert len(r.json['without_findings']) == 0
        assert len(r.json['marked_review']) == 0
        assert len(r.json['ongoing']) == 0

        r = client.get('/api/v1/overviews/analyses/finalized/')
        assert isinstance(r.json, list) and len(r.json) == 1


def get_non_filtered_alleles(session):

    allele_ids_genepanels = session.query(
        workflow.AnalysisInterpretation.genepanel_name,
        workflow.AnalysisInterpretation.genepanel_version,
        allele.Allele.id
    ).join(
        genotype.Genotype.alleles,
        sample.Sample,
        sample.Analysis
    ).filter(
        workflow.AnalysisInterpretation.analysis_id == sample.Analysis.id,
        workflow.AnalysisInterpretation.status == 'Not started'
    ).distinct().all()

    # Subtract ongoing or marked review alleleinterpretations
    def get_sub_query(status):
        return session.query(allele.Allele.id).join(
            workflow.AlleleInterpretation
        ).filter(
            workflow.AlleleInterpretation.status == status
        )

    ongoing_allele_ids = session.query(allele.Allele.id).join(
        workflow.AlleleInterpretation
    ).filter(
        or_(
            and_(  # marked review
                allele.Allele.id.in_(get_sub_query('Not started')),
                allele.Allele.id.in_(get_sub_query('Done')),
            ),
            allele.Allele.id.in_(get_sub_query('Ongoing'))  # ongoing
        )
    ).distinct(allele.Allele.id).all()

    ongoing_allele_ids = [o[0] for o in ongoing_allele_ids]
    gp_allele_ids = defaultdict(set)
    for gp_name, gp_key, allele_id in allele_ids_genepanels:
        if allele_id in ongoing_allele_ids:
            continue
        gp_key = (gp_name, gp_key)
        gp_allele_ids[gp_key].add(allele_id)

    result = AlleleFilter(session).filter_alleles(gp_allele_ids)
    for key in gp_allele_ids:
        gp_allele_ids[key] = set(result[key]['allele_ids'])
    return gp_allele_ids


def get_allele_not_started(session):

    # Alleles contributed from analyses
    gp_allele_ids = get_non_filtered_alleles(session)  # {('HBOC', 'v01'): [1, 2, 3], ...}

    # Alleles contributed from AlleleInterpretations
    alleleinterpretation_allele_ids = session.query(
        workflow.AlleleInterpretation.allele_id,
        workflow.AlleleInterpretation.genepanel_name,
        workflow.AlleleInterpretation.genepanel_version
    ).filter(
        workflow.AlleleInterpretation.status == 'Not started'
    ).all()

    for allele_id, gp_name, gp_version in alleleinterpretation_allele_ids:
        gp_key = (gp_name, gp_version)
        gp_allele_ids[gp_key].add(allele_id)

    return gp_allele_ids


def get_allele_alleleinterpretation_started(session):

    # Alleles contributed from AlleleInterpretations
    alleleinterpretation_allele_ids = session.query(
        workflow.AlleleInterpretation.allele_id,
        workflow.AlleleInterpretation.genepanel_name,
        workflow.AlleleInterpretation.genepanel_version
    ).filter(
        or_(
            workflow.AlleleInterpretation.status == 'Ongoing',
            workflow.AlleleInterpretation.status == 'Done'
        )
    ).all()

    gp_allele_ids = defaultdict(set)
    for allele_id, gp_name, gp_version in alleleinterpretation_allele_ids:
        gp_key = (gp_name, gp_version)
        gp_allele_ids[gp_key].add(allele_id)

    return gp_allele_ids


def get_diff_gp_allele_ids(left, right):
    diff_gp_allele_ids = dict()
    for gp_key, allele_ids in left.iteritems():
        if gp_key in right:
            diff_gp_allele_ids[gp_key] = left[gp_key] - right[gp_key]
        else:
            diff_gp_allele_ids[gp_key] = left[gp_key]

    return diff_gp_allele_ids


def check_items(gp_allele_ids, items, should_include=True, check_length=True):
    match_cnt = 0

    not_matched = list(items)

    if not should_include:  # Doesn't make sense to check length
        check_length = False

    for gp_key, allele_ids in gp_allele_ids.iteritems():
        for allele_id in allele_ids:
            match = next((
                i for i in items
                if i['allele']['id'] == allele_id and
                i['genepanel']['name'] == gp_key[0] and
                i['genepanel']['version'] == gp_key[1]
            ), None)
            if should_include:
                assert match
                not_matched.remove(match)
                match_cnt += 1
            else:
                assert not match

    if check_length:
        assert match_cnt == len(items), 'Items not matched: {}'.format(not_matched)


class TestAlleleOverview(object):

    @pytest.mark.overviewallele(order=0)
    def test_not_started_initial(self, test_database, client, session):
        """
        Do some initial checks.
        """
        test_database.refresh()

        # Get data to compare against
        initial_gp_allele_ids = get_allele_not_started(session)

        r = client.get('/api/v1/overviews/alleles/')

        assert len(r.json['ongoing']) == 0
        assert set([a['allele']['id'] for a in r.json['missing_alleleassessment']]) == \
            set(itertools.chain.from_iterable(initial_gp_allele_ids.values()))
        assert len(r.json['marked_review']) == 0

        # Check missing_alleleassesment in detail
        check_items(initial_gp_allele_ids, r.json['missing_alleleassessment'])

        # Finalized
        r = client.get('/api/v1/overviews/alleles/finalized/')
        assert isinstance(r.json, list) and len(r.json) == 0

        ##
        # Start one analysis ->
        # alleles only existing in this analysis should disappear
        ##

        wh = WorkflowHelper('analysis', 4)
        wh.start_interpretation('testuser1')

        gp_allele_ids = get_allele_not_started(session)

        r = client.get('/api/v1/overviews/alleles/')
        assert len(r.json['ongoing']) == 0
        assert len(r.json['marked_review']) == 0

        check_items(gp_allele_ids, r.json['missing_alleleassessment'])

        # Ensure that the alleles are now gone from the list
        diff_gp_allele_ids = get_diff_gp_allele_ids(initial_gp_allele_ids, gp_allele_ids)
        check_items(diff_gp_allele_ids, r.json['missing_alleleassessment'], should_include=False)

    @pytest.mark.overviewallele(order=1)
    def test_not_started_start_interpretation(self, test_database, client, session):
        """
        Start one alleleinterpretation -> disappear from missing list and move into ongoing
         - case 1: part of not started analysis with same genepanel
         - case 2: part of not started analysis with different genepanel
         - case 3: not part of analysis
        """
        test_database.refresh()

        # Case 1:
        # Analysis 1 (HBOC, v01) has overlapping alleleinterpretations
        # with AlleleInterpretation 1 (allele id 1)
        wh = WorkflowHelper('allele', 1, genepanel=('HBOC', 'v01'))
        wh.start_interpretation('testuser1')

        not_started_gp_allele_ids = get_allele_not_started(session)
        started_gp_allele_ids = get_allele_alleleinterpretation_started(session)

        # Ensure started id is not anymore in set
        started_allele_id = session.query(workflow.AlleleInterpretation.allele_id).filter(
            workflow.AlleleInterpretation.id == 1
        ).scalar()

        assert any(started_allele_id in a for a in started_gp_allele_ids.values())
        assert all(started_allele_id not in a for a in not_started_gp_allele_ids.values())

        # Check that all entries are included as they should
        r = client.get('/api/v1/overviews/alleles/')

        assert len(r.json['marked_review']) == 0
        check_items(not_started_gp_allele_ids, r.json['missing_alleleassessment'])
        check_items(started_gp_allele_ids, r.json['missing_alleleassessment'], should_include=False)
        check_items(started_gp_allele_ids, r.json['ongoing'])

        # Case 2:
        # Analysis 1 (HBOC, v01) has overlapping alleleinterpretations
        # with AlleleInterpretation 2 (allele id 3)
        wh = WorkflowHelper('allele', 3, genepanel=('HBOCUTV', 'v01'))
        wh.start_interpretation('testuser1')

        not_started_gp_allele_ids = get_allele_not_started(session)
        started_gp_allele_ids = get_allele_alleleinterpretation_started(session)

        # Ensure started id is not anymore in set
        started_allele_id = session.query(workflow.AlleleInterpretation.allele_id).filter(
            workflow.AlleleInterpretation.id == 2
        ).scalar()

        assert all(started_allele_id not in a for a in not_started_gp_allele_ids.values())
        assert any(started_allele_id in a for a in started_gp_allele_ids.values())

        # Check that all entries are included as they should
        r = client.get('/api/v1/overviews/alleles/')

        assert len(r.json['marked_review']) == 0
        check_items(not_started_gp_allele_ids, r.json['missing_alleleassessment'])
        check_items(started_gp_allele_ids, r.json['missing_alleleassessment'], should_include=False)
        check_items(started_gp_allele_ids, r.json['ongoing'])

        # Case 3:
        # Analysis 1 (HBOC, v01) has overlapping alleleinterpretations
        # with AlleleInterpretation 3 (allele id 4)
        # We first start Analysis 1 to exclude it, since we want to test case when no analysis.

        wh = WorkflowHelper('analysis', 1)
        wh.start_interpretation('testuser1')

        wh = WorkflowHelper('allele', 4, genepanel=('HBOC', 'v01'))
        wh.start_interpretation('testuser1')

        not_started_gp_allele_ids = get_allele_not_started(session)
        started_gp_allele_ids = get_allele_alleleinterpretation_started(session)

        # Ensure started id is not anymore in set
        started_allele_id = session.query(workflow.AlleleInterpretation.allele_id).filter(
            workflow.AlleleInterpretation.id == 3
        ).scalar()

        assert all(started_allele_id not in a for a in not_started_gp_allele_ids.values())
        assert any(started_allele_id in a for a in started_gp_allele_ids.values())

        # Check that all entries are included as they should
        r = client.get('/api/v1/overviews/alleles/')

        assert len(r.json['marked_review']) == 0
        check_items(not_started_gp_allele_ids, r.json['missing_alleleassessment'])
        check_items(started_gp_allele_ids, r.json['missing_alleleassessment'], should_include=False)
        check_items(started_gp_allele_ids, r.json['ongoing'])

    @pytest.mark.overviewallele(order=2)
    def test_not_started_with_valid_alleleassessment(self, test_database, client, session, with_finding_classification):
        """
        Has valid alleleassessment and part of analysis only -> disappear from missing list

        - case 1: allele has alleleinterpretation and analysis: not disappear
        - case 2: allele has only analysis: disappear
        """
        test_database.refresh()

        # Case 1:
        # AlleleInterpretation 6 is overlapping only with Analysis 2

        allele_id = session.query(workflow.AlleleInterpretation.allele_id).filter(
            workflow.AlleleInterpretation.id == 6
        ).scalar()

        aa = assessment.AlleleAssessment(
            classification=with_finding_classification['value'],  # Actual value doesn't matter as long as not outdated
            allele_id=allele_id,
            genepanel_name='HBOCUTV',
            genepanel_version='v01'
        )

        # Should be in list before
        r = client.get('/api/v1/overviews/alleles/')
        check_items({('HBOC', 'v01'): [allele_id]}, r.json['missing_alleleassessment'], check_length=False)

        session.add(aa)
        session.commit()

        # Should be in list after
        r = client.get('/api/v1/overviews/alleles/')
        check_items({('HBOC', 'v01'): [allele_id]}, r.json['missing_alleleassessment'], check_length=False)

        # Case 2:
        # Analysis 3 has no overlapping AlleleInterpretation

        interpretation_id = ih.get_interpretation_id_of_last('analysis', 3)
        interpretation = ih.get_interpretation('analysis', 3, interpretation_id)
        allele_id = ih.get_alleles('analysis', 3, interpretation_id, interpretation['allele_ids'])[0]['id']

        aa = assessment.AlleleAssessment(
            classification=with_finding_classification['value'],
            allele_id=allele_id,
            genepanel_name='HBOCUTV',
            genepanel_version='v01'
        )

        # Should be in list before
        r = client.get('/api/v1/overviews/alleles/')
        check_items({('HBOCUTV', 'v01'): [allele_id]}, r.json['missing_alleleassessment'], check_length=False)

        session.add(aa)
        session.commit()

        # Should not be in list after
        r = client.get('/api/v1/overviews/alleles/')
        check_items({('HBOCUTV', 'v01'): [allele_id]}, r.json['missing_alleleassessment'], should_include=False)

    @pytest.mark.overviewallele(order=3)
    def test_not_started_with_valid_alleleassessment(self, test_database, client, session, with_finding_classification):
        """
        Has outdated alleleassessment -> appear in missing list
        """
        test_database.refresh()

        interpretation_id = ih.get_interpretation_id_of_last('analysis', 3)
        interpretation = ih.get_interpretation('analysis', 3, interpretation_id)
        allele_id = ih.get_alleles('analysis', 3, interpretation_id, interpretation['allele_ids'])[0]['id']

        timedelta = datetime.timedelta(days=with_finding_classification['outdated_after_days'] + 1)
        aa = assessment.AlleleAssessment(
            classification=with_finding_classification['value'],
            allele_id=allele_id,
            genepanel_name='HBOCUTV',
            genepanel_version='v01',
            date_created=datetime.datetime.now(pytz.utc) - timedelta
        )

        # Should be in list before
        r = client.get('/api/v1/overviews/alleles/')
        check_items({('HBOCUTV', 'v01'): [allele_id]}, r.json['missing_alleleassessment'], check_length=False)

        session.add(aa)
        session.commit()

        # Should still be in list after
        r = client.get('/api/v1/overviews/alleles/')
        check_items({('HBOCUTV', 'v01'): [allele_id]}, r.json['missing_alleleassessment'], check_length=False)

    @pytest.mark.overviewallele(order=4)
    def test_other_categories(self, test_database, client, session):
        """
        Test the other categories:
        - ongoing
        - marked_review
        - finalized
        """
        test_database.refresh()

        wh = WorkflowHelper('allele', 1, genepanel=('HBOC', 'v01'))

        # Ongoing
        interpretation = wh.start_interpretation('testuser1')
        r = client.get('/api/v1/overviews/alleles/')
        check_items({('HBOC', 'v01'): interpretation['allele_ids']}, r.json['ongoing'])

        # Marked review
        wh.perform_review_round(interpretation)
        r = client.get('/api/v1/overviews/alleles/')
        check_items({('HBOC', 'v01'): interpretation['allele_ids']}, r.json['marked_review'])

        # Finalized
        interpretation = wh.start_interpretation('testuser2')
        wh.perform_finalize_round(interpretation)
        r = client.get('/api/v1/overviews/alleles/finalized/')
        check_items({('HBOC', 'v01'): interpretation['allele_ids']}, r.json)
