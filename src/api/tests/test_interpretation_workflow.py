import datetime
import pytest

from vardb.datamodel import assessment, user as user_model

from api.tests.workflow_helper import WorkflowHelper
from api.tests import interpretation_helper as ih

"""
Test the interpretation workflow of
 - a sample/analysis
 - a single variant

The single variant is chosen not be included in the sample/analysis.
So any assessments done in either sample or variant
workflow won't affect each other.

The tests for variant and sample workflows are similar.
The differences are handled using parametrized tests, some
workflow specific test fixture and branching based on workflow.

"""

ANALYSIS_ID = 2  # analysis_id = 2, allele 1-6
ALLELE_ID = (
    18
)  # allele id 18, brca2 c.1275A>G,  GRCh37/13-32906889-32906890-A-G?gp_name=HBOCUTV&gp_version=v01
FILTERCONFIG_ID = 1

ANALYSIS_ALLELE_IDS = [1, 3, 4, 7, 12, 13]

ANALYSIS_USERNAMES = ["testuser1", "testuser2", "testuser3"]  # username for each round
ALLELE_USERNAMES = ["testuser4", "testuser1", "testuser2"]


@pytest.fixture(scope="module")
def analysis_wh():
    return WorkflowHelper("analysis", ANALYSIS_ID, filterconfig_id=FILTERCONFIG_ID)


@pytest.fixture(scope="module")
def allele_wh():
    return WorkflowHelper("allele", ALLELE_ID, genepanel=("HBOCUTV", "v01"))


def update_user_config(session, username, user_config):

    user = session.query(user_model.User).filter(user_model.User.username == username).one()

    user.config = user_config
    session.commit()


class TestAnalysisInterpretationWorkflow(object):
    """
    Tests the whole workflow of
    interpretations on one analysis.

    - Interpretation -> Not ready
    - Not ready -> Interpretation
    - Interpretation -> Review
    - Review -> Medical review
    - Finalize
    - Reopen -> one round -> finalize
    """

    @pytest.mark.ai(order=0)
    def test_init_data(self, test_database):
        test_database.refresh()

    @pytest.mark.ai(order=1)
    def test_round_one_notready(self, analysis_wh):
        interpretation = analysis_wh.start_interpretation(ANALYSIS_USERNAMES[0])
        analysis_wh.perform_round(
            interpretation, "Not ready comment", new_workflow_status="Not ready"
        )

    @pytest.mark.ai(order=1)
    def test_round_two_interpretation(self, analysis_wh):
        interpretation = analysis_wh.start_interpretation(ANALYSIS_USERNAMES[0])
        analysis_wh.perform_round(
            interpretation, "Interpretation comment", new_workflow_status="Interpretation"
        )

    @pytest.mark.ai(order=1)
    def test_round_three_review(self, analysis_wh):
        interpretation = analysis_wh.start_interpretation(ANALYSIS_USERNAMES[0])
        analysis_wh.perform_round(interpretation, "Review comment", new_workflow_status="Review")

    @pytest.mark.ai(order=1)
    def test_round_four_review(self, analysis_wh):
        interpretation = analysis_wh.start_interpretation(ANALYSIS_USERNAMES[0])
        analysis_wh.perform_round(
            interpretation, "Medical review comment", new_workflow_status="Medical review"
        )

    @pytest.mark.ai(order=2)
    def test_round_five_finalize(self, analysis_wh):
        interpretation = analysis_wh.start_interpretation(ANALYSIS_USERNAMES[1])
        analysis_wh.perform_finalize_round(interpretation, "Finalize comment")

    @pytest.mark.ai(order=3)
    def test_round_three_reopen_and_finalize(self, analysis_wh):
        analysis_wh.reopen(ANALYSIS_USERNAMES[2])
        interpretation = analysis_wh.start_interpretation(ANALYSIS_USERNAMES[2])
        analysis_wh.perform_reopened_round(interpretation, "Reopened comment")


class TestAlleleInterpretationWorkflow(object):
    """
    Tests the whole workflow of
    interpretations on one allele.

    - Interpretation -> Review
    - Finalize
    - Reopen -> one round -> finalize
    """

    @pytest.mark.ai(order=0)
    def test_init_data(self, test_database):
        test_database.refresh()

    @pytest.mark.ai(order=1)
    def test_round_one_review(self, allele_wh):
        interpretation = allele_wh.start_interpretation(ALLELE_USERNAMES[0])
        allele_wh.perform_round(interpretation, "Review comment", new_workflow_status="Review")

    @pytest.mark.ai(order=2)
    def test_round_two_finalize(self, allele_wh):
        interpretation = allele_wh.start_interpretation(ALLELE_USERNAMES[1])
        allele_wh.perform_finalize_round(interpretation, "Finalize comment")

    @pytest.mark.ai(order=3)
    def test_round_three_reopen_and_finalize(self, allele_wh):
        allele_wh.reopen(ALLELE_USERNAMES[2])
        interpretation = allele_wh.start_interpretation(ALLELE_USERNAMES[2])
        allele_wh.perform_reopened_round(interpretation, "Reopened comment")


class TestOther(object):
    """
    Tests other scenarios not covered in normal workflow
    """

    @pytest.mark.ai(order=0)
    def test_disallow_referenceassessment_no_alleleassessment(self, test_database, session):
        """
        Test case where one tries to create referenceassessments for alleles where
        no alleleassessments will be created at the same time.
        """

        test_database.refresh()

        # Create dummy alleleassessment
        aa = assessment.AlleleAssessment(
            allele_id=1,
            classification="1",
            evaluation={},
            genepanel_name="HBOC",
            genepanel_version="v01",
        )
        session.add(aa)
        session.commit()

        interpretation = ih.start_interpretation(
            "allele", 1, "testuser1", extra={"gp_name": "HBOC", "gp_version": "v01"}
        )

        r = ih.get_alleles("allele", 1, interpretation["id"], [1])
        assert r.status_code == 200
        alleles = r.get_json()

        # Reuse alleleassessment
        alleleassessments = [{"allele_id": 1, "reuse": True, "presented_alleleassessment_id": 1}]
        # Create new referenceassessment
        referenceassessments = [
            {
                "reference_id": 1,
                "allele_id": 1,
                "evaluation": {"some": "data"},
                "genepanel_name": "HBOC",
                "genepanel_version": "v01",
            }
        ]
        attachments = []
        allelereports = []
        annotations = [
            {"allele_id": a["id"], "annotation_id": a["annotation"]["annotation_id"]}
            for a in alleles
        ]
        custom_annotations = []

        r = ih.finalize(
            "allele",
            1,
            annotations,
            custom_annotations,
            alleleassessments,
            referenceassessments,
            allelereports,
            attachments,
            "testuser1",
        )
        assert (
            "Trying to create referenceassessment for allele, while not also creating alleleassessment"
            in str(r.get_json()["message"])
        )
        assert r.status_code == 500

    @pytest.mark.ai(order=1)
    def test_reusing_superceded_referenceassessment(self, test_database, session):
        """
        Test case where one tries to reuse superceded referenceassessment.
        """

        test_database.refresh()

        # Create dummy referenceassessment
        ra = assessment.ReferenceAssessment(
            allele_id=1,
            reference_id=1,
            evaluation={},
            genepanel_name="HBOC",
            genepanel_version="v01",
            date_superceeded=datetime.datetime.now(),
        )
        session.add(ra)
        session.commit()

        # Will get id = 2
        ra = assessment.ReferenceAssessment(
            allele_id=1,
            reference_id=1,
            evaluation={},
            genepanel_name="HBOC",
            genepanel_version="v01",
            previous_assessment_id=1,
        )

        session.add(ra)
        session.commit()

        interpretation = ih.start_interpretation(
            "allele", 1, "testuser1", extra={"gp_name": "HBOC", "gp_version": "v01"}
        )

        r = ih.get_alleles("allele", 1, interpretation["id"], [1])
        assert r.status_code == 200
        alleles = r.get_json()

        # Reuse alleleassessment
        alleleassessments = [
            {
                "allele_id": 1,
                "classification": "1",
                "evaluation": {},
                "genepanel_name": "HBOC",
                "genepanel_version": "v01",
            }
        ]
        # Create new referenceassessment
        referenceassessments = [{"id": 1, "reference_id": 1, "allele_id": 1}]  # outdated
        attachments = []
        allelereports = []
        annotations = [
            {"allele_id": a["id"], "annotation_id": a["annotation"]["annotation_id"]}
            for a in alleles
        ]
        custom_annotations = []

        r = ih.finalize(
            "allele",
            1,
            annotations,
            custom_annotations,
            alleleassessments,
            referenceassessments,
            allelereports,
            attachments,
            "testuser1",
        )
        assert "Found no matching referenceassessment" in r.get_json()["message"]

    @pytest.mark.ai(order=2)
    def test_reusing_superceded_alleleassessment(self, test_database, session):
        """
        Test case where one tries to reuse superceded referenceassessment.
        """

        test_database.refresh()

        # Create dummy alleleassessment
        aa = assessment.AlleleAssessment(
            allele_id=1,
            classification="1",
            evaluation={},
            genepanel_name="HBOC",
            genepanel_version="v01",
            date_superceeded=datetime.datetime.now(),
        )
        session.add(aa)
        session.commit()

        # Will get id = 2
        aa = assessment.AlleleAssessment(
            allele_id=1,
            classification="2",
            evaluation={},
            genepanel_name="HBOC",
            genepanel_version="v01",
            previous_assessment_id=1,
        )
        session.add(aa)
        session.commit()

        interpretation = ih.start_interpretation(
            "allele", 1, "testuser1", extra={"gp_name": "HBOC", "gp_version": "v01"}
        )

        r = ih.get_alleles("allele", 1, interpretation["id"], [1])
        assert r.status_code == 200
        alleles = r.get_json()

        # Reuse alleleassessment
        alleleassessments = [
            {"allele_id": 1, "reuse": True, "presented_alleleassessment_id": 1}
        ]  # Outdated

        referenceassessments = []
        attachments = []
        allelereports = []
        annotations = [
            {"allele_id": a["id"], "annotation_id": a["annotation"]["annotation_id"]}
            for a in alleles
        ]
        custom_annotations = []

        r = ih.finalize(
            "allele",
            1,
            annotations,
            custom_annotations,
            alleleassessments,
            referenceassessments,
            allelereports,
            attachments,
            "testuser1",
        )
        assert "Found no matching alleleassessment" in r.get_json()["message"]


class TestFinalizationRequirements:
    @pytest.mark.ai(order=1)
    def test_required_workflow_status_allele(self, test_database, session):
        """
        Test finalizing when in and when not in the required workflow status.
        """

        test_database.refresh()

        # Default user id is 1
        user_config = {
            "workflows": {"allele": {"finalize_requirements": {"workflow_status": ["Review"]}}}
        }
        user = session.query(user_model.User).filter(user_model.User.id == 1).one()

        user.config = user_config
        session.commit()

        interpretation = ih.start_interpretation(
            "allele", 1, "testuser1", extra={"gp_name": "HBOC", "gp_version": "v01"}
        )

        r = ih.get_alleles("allele", 1, interpretation["id"], [1])

        assert r.status_code == 200
        alleles = r.get_json()

        # Reuse alleleassessment
        alleleassessments = [
            {
                "allele_id": 1,
                "classification": "1",
                "evaluation": {},
                "genepanel_name": "HBOC",
                "genepanel_version": "v01",
            }
        ]
        referenceassessments = []
        attachments = []
        allelereports = []
        annotations = [
            {"allele_id": a["id"], "annotation_id": a["annotation"]["annotation_id"]}
            for a in alleles
        ]
        custom_annotations = []

        r = ih.finalize(
            "allele",
            1,
            annotations,
            custom_annotations,
            alleleassessments,
            referenceassessments,
            allelereports,
            attachments,
            "testuser1",
            allele_ids=[1],
        )
        assert r.status_code == 500
        assert (
            "Cannot finalize: Interpretation's workflow status is in one of required ones"
            in r.get_json()["message"]
        )

        # Send to review, and try again
        r = ih.mark_review(
            "allele",
            1,
            {
                "annotations": annotations,
                "custom_annotations": custom_annotations,
                "alleleassessments": alleleassessments,
                "allelereports": allelereports,
            },
            "testuser1",
        )
        r.status_code == 200

        ih.start_interpretation(
            "allele", 1, "testuser1", extra={"gp_name": "HBOC", "gp_version": "v01"}
        )

        r = ih.finalize(
            "allele",
            1,
            annotations,
            custom_annotations,
            alleleassessments,
            referenceassessments,
            allelereports,
            attachments,
            "testuser1",
            allele_ids=[1],
        )
        assert r.status_code == 200

    @pytest.mark.ai(order=2)
    def test_required_workflow_status_analysis(self, test_database, session):
        """
        Test finalizing when in and when not in the required workflow status.
        """

        test_database.refresh()

        # Default user id is 1
        user_config = {
            "workflows": {
                "analysis": {"finalize_requirements": {"workflow_status": ["Medical review"]}}
            }
        }
        update_user_config(session, "testuser1", user_config)

        interpretation = ih.start_interpretation(
            "analysis", 1, "testuser1", extra={"gp_name": "HBOC", "gp_version": "v01"}
        )

        filtered_allele_ids = ih.get_filtered_alleles(
            "analysis", 1, interpretation["id"], filterconfig_id=1
        ).get_json()

        r = ih.get_alleles("analysis", 1, interpretation["id"], filtered_allele_ids["allele_ids"])
        assert r.status_code == 200
        alleles = r.get_json()

        # Reuse alleleassessment
        alleleassessments = [
            {
                "allele_id": a["id"],
                "classification": "1",
                "evaluation": {},
                "genepanel_name": "HBOC",
                "genepanel_version": "v01",
            }
            for a in alleles
        ]
        referenceassessments = []
        attachments = []
        allelereports = []
        annotations = [
            {"allele_id": a["id"], "annotation_id": a["annotation"]["annotation_id"]}
            for a in alleles
        ]
        custom_annotations = []

        r = ih.finalize(
            "analysis",
            1,
            annotations,
            custom_annotations,
            alleleassessments,
            referenceassessments,
            allelereports,
            attachments,
            "testuser1",
            allele_ids=filtered_allele_ids["allele_ids"],
            excluded_allele_ids=filtered_allele_ids["excluded_allele_ids"],
        )
        assert (
            "Cannot finalize: Interpretation's workflow status is in one of required ones"
            in r.get_json()["message"]
        )

        # Send to review, and try again
        ih.mark_medicalreview(
            "analysis",
            1,
            ih.round_template(
                annotations=annotations,
                custom_annotations=custom_annotations,
                alleleassessments=alleleassessments,
                allelereports=allelereports,
                allele_ids=filtered_allele_ids["allele_ids"],
                excluded_allele_ids=filtered_allele_ids["excluded_allele_ids"],
            ),
            "testuser1",
        )

        interpretation = ih.start_interpretation(
            "analysis", 1, "testuser1", extra={"gp_name": "HBOC", "gp_version": "v01"}
        )

        ih.finalize(
            "analysis",
            1,
            annotations,
            custom_annotations,
            alleleassessments,
            referenceassessments,
            allelereports,
            attachments,
            "testuser1",
            allele_ids=filtered_allele_ids["allele_ids"],
            excluded_allele_ids=filtered_allele_ids["excluded_allele_ids"],
        )

    @pytest.mark.ai(order=2)
    def test_allow_technical(self, test_database, session):
        """
        Test finalization requirement allow_technical
        """

        test_database.refresh()

        # Default user is testuser1
        user_config = {
            "workflows": {
                "analysis": {
                    "finalize_requirements": {
                        "allow_technical": False,
                        "allow_notrelevant": False,
                        "allow_unclassified": False,
                    }
                }
            }
        }
        update_user_config(session, "testuser1", user_config)

        interpretation = ih.start_interpretation(
            "analysis", 1, "testuser1", extra={"gp_name": "HBOC", "gp_version": "v01"}
        )

        filtered_allele_ids = ih.get_filtered_alleles(
            "analysis", 1, interpretation["id"], filterconfig_id=1
        ).get_json()

        r = ih.get_alleles("analysis", 1, interpretation["id"], filtered_allele_ids["allele_ids"])
        assert r.status_code == 200
        alleles = r.get_json()

        alleleassessments = [
            {
                "allele_id": a["id"],
                "classification": "1",
                "evaluation": {},
                "genepanel_name": "HBOC",
                "genepanel_version": "v01",
            }
            for a in alleles
        ]

        # Make one variant unclassified, but reported as technical
        notrelevant_allele_ids = []
        technical_allele_ids = [alleleassessments[0]["allele_id"]]
        alleleassessments = alleleassessments[1:]
        referenceassessments = []
        attachments = []
        allelereports = []
        annotations = [
            {"allele_id": a["id"], "annotation_id": a["annotation"]["annotation_id"]}
            for a in alleles
        ]
        custom_annotations = []

        # allow_technical is False, so it should fail
        r = ih.finalize(
            "analysis",
            1,
            annotations,
            custom_annotations,
            alleleassessments,
            referenceassessments,
            allelereports,
            attachments,
            "testuser1",
            allele_ids=filtered_allele_ids["allele_ids"],
            excluded_allele_ids=filtered_allele_ids["excluded_allele_ids"],
            technical_allele_ids=technical_allele_ids,
            notrelevant_allele_ids=notrelevant_allele_ids,
        )
        assert r.status_code == 500
        assert "Missing alleleassessments for allele ids 1" in r.get_json()["message"]

        # Allow technical and try again
        user_config = {
            "workflows": {
                "analysis": {
                    "finalize_requirements": {
                        "allow_technical": True,
                        "allow_notrelevant": False,
                        "allow_unclassified": False,
                    }
                }
            }
        }
        update_user_config(session, "testuser1", user_config)

        r = ih.finalize(
            "analysis",
            1,
            annotations,
            custom_annotations,
            alleleassessments,
            referenceassessments,
            allelereports,
            attachments,
            "testuser1",
            allele_ids=filtered_allele_ids["allele_ids"],
            excluded_allele_ids=filtered_allele_ids["excluded_allele_ids"],
            technical_allele_ids=technical_allele_ids,
            notrelevant_allele_ids=notrelevant_allele_ids,
        )
        assert r.status_code == 200

    @pytest.mark.ai(order=3)
    def test_allow_notrelevant(self, test_database, session):
        """
        Test finalization requirement allow_notrelevant
        """

        test_database.refresh()

        # Default user is testuser1
        user_config = {
            "workflows": {
                "analysis": {
                    "finalize_requirements": {
                        "allow_technical": False,
                        "allow_notrelevant": False,
                        "allow_unclassified": False,
                    }
                }
            }
        }
        update_user_config(session, "testuser1", user_config)

        interpretation = ih.start_interpretation(
            "analysis", 1, "testuser1", extra={"gp_name": "HBOC", "gp_version": "v01"}
        )

        filtered_alleles = ih.get_filtered_alleles(
            "analysis", 1, interpretation["id"], filterconfig_id=1
        ).get_json()

        r = ih.get_alleles("analysis", 1, interpretation["id"], filtered_alleles["allele_ids"])

        assert r.status_code == 200
        alleles = r.get_json()

        alleleassessments = [
            {
                "allele_id": a["id"],
                "classification": "1",
                "evaluation": {},
                "genepanel_name": "HBOC",
                "genepanel_version": "v01",
            }
            for a in alleles
        ]

        # Make one variant unclassified, but reported as not relevant
        notrelevant_allele_ids = [alleleassessments[0]["allele_id"]]
        technical_allele_ids = []
        alleleassessments = alleleassessments[1:]
        referenceassessments = []
        attachments = []
        allelereports = []
        annotations = [
            {"allele_id": a["id"], "annotation_id": a["annotation"]["annotation_id"]}
            for a in alleles
        ]
        custom_annotations = []

        # allow_notrelevant is False, so it should fail
        r = ih.finalize(
            "analysis",
            1,
            annotations,
            custom_annotations,
            alleleassessments,
            referenceassessments,
            allelereports,
            attachments,
            "testuser1",
            allele_ids=filtered_alleles["allele_ids"],
            excluded_allele_ids=filtered_alleles["excluded_allele_ids"],
            technical_allele_ids=technical_allele_ids,
            notrelevant_allele_ids=notrelevant_allele_ids,
        )
        assert r.status_code == 500
        assert "Missing alleleassessments for allele ids 1" in r.get_json()["message"]

        # Allow notrelevant and try again
        user_config = {
            "workflows": {
                "analysis": {
                    "finalize_requirements": {
                        "allow_technical": False,
                        "allow_notrelevant": True,
                        "allow_unclassified": False,
                    }
                }
            }
        }
        update_user_config(session, "testuser1", user_config)

        r = ih.finalize(
            "analysis",
            1,
            annotations,
            custom_annotations,
            alleleassessments,
            referenceassessments,
            allelereports,
            attachments,
            "testuser1",
            allele_ids=filtered_alleles["allele_ids"],
            excluded_allele_ids=filtered_alleles["excluded_allele_ids"],
            technical_allele_ids=technical_allele_ids,
            notrelevant_allele_ids=notrelevant_allele_ids,
        )
        assert r.status_code == 200

    @pytest.mark.ai(order=4)
    def test_allow_unclassified(self, test_database, session):
        """
        Test finalization requirement allow_unclassified
        """

        test_database.refresh()

        # Default user is testuser1
        user_config = {
            "workflows": {
                "analysis": {
                    "finalize_requirements": {
                        "allow_technical": False,
                        "allow_notrelevant": False,
                        "allow_unclassified": False,
                    }
                }
            }
        }
        update_user_config(session, "testuser1", user_config)

        interpretation = ih.start_interpretation(
            "analysis", 1, "testuser1", extra={"gp_name": "HBOC", "gp_version": "v01"}
        )

        filtered_alleles = ih.get_filtered_alleles(
            "analysis", 1, interpretation["id"], filterconfig_id=1
        ).get_json()

        r = ih.get_alleles("analysis", 1, interpretation["id"], filtered_alleles["allele_ids"])

        assert r.status_code == 200
        alleles = r.get_json()

        alleleassessments = [
            {
                "allele_id": a["id"],
                "classification": "1",
                "evaluation": {},
                "genepanel_name": "HBOC",
                "genepanel_version": "v01",
            }
            for a in alleles
        ]

        # Make two variants unclassified, one reported as technical and one not relevant
        notrelevant_allele_ids = [alleleassessments[0]["allele_id"]]
        technical_allele_ids = [alleleassessments[1]["allele_id"]]
        alleleassessments = alleleassessments[2:]
        referenceassessments = []
        attachments = []
        allelereports = []
        annotations = [
            {"allele_id": a["id"], "annotation_id": a["annotation"]["annotation_id"]}
            for a in alleles
        ]
        custom_annotations = []

        # allow_unclassified is False, so it should fail
        r = ih.finalize(
            "analysis",
            1,
            annotations,
            custom_annotations,
            alleleassessments,
            referenceassessments,
            allelereports,
            attachments,
            "testuser1",
            allele_ids=filtered_alleles["allele_ids"],
            excluded_allele_ids=filtered_alleles["excluded_allele_ids"],
            technical_allele_ids=technical_allele_ids,
            notrelevant_allele_ids=notrelevant_allele_ids,
        )
        assert r.status_code == 500
        assert "Missing alleleassessments for allele ids 1,2" in r.get_json()["message"]

        # Allow unclassified and try again
        # (allow_unclassified implies allow_technical and allow_notrelevant)
        user_config = {
            "workflows": {
                "analysis": {
                    "finalize_requirements": {
                        "allow_technical": False,
                        "allow_notrelevant": False,
                        "allow_unclassified": True,
                    }
                }
            }
        }
        update_user_config(session, "testuser1", user_config)

        r = ih.finalize(
            "analysis",
            1,
            annotations,
            custom_annotations,
            alleleassessments,
            referenceassessments,
            allelereports,
            attachments,
            "testuser1",
            allele_ids=filtered_alleles["allele_ids"],
            excluded_allele_ids=filtered_alleles["excluded_allele_ids"],
            technical_allele_ids=technical_allele_ids,
            notrelevant_allele_ids=notrelevant_allele_ids,
        )
        assert r.status_code == 200
