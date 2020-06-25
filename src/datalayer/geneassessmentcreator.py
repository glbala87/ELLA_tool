import datetime
import pytz
from typing import Dict
from vardb.datamodel import assessment, sample


from vardb.datamodel.assessment import GeneAssessment
from api import ApiError

import logging

log = logging.getLogger(__name__)


class GeneAssessmentCreator(object):
    def __init__(self, session):
        self.session = session

    def create_from_data(
        self,
        user_id: int,
        usergroup_id: int,
        gene_id: int,
        genepanel_name: str,
        genepanel_version: str,
        evaluation: Dict[str, Dict[str, str]],
        presented_geneassessment_id: int = None,
        analysis_id: int = None,
    ) -> assessment.GeneAssessment:
        """
        Takes in geneassessment data and creates a new GeneAssessment object.

        The created object is not added to session/database.
        """

        if analysis_id:
            assert (
                self.session.query(sample.Analysis)
                .filter(sample.Analysis.id == analysis_id)
                .count()
                == 1
            )

        existing_assessment = (
            self.session.query(assessment.GeneAssessment)
            .filter(
                assessment.GeneAssessment.gene_id == gene_id,
                assessment.GeneAssessment.date_superceeded.is_(
                    None
                ),  # Only allowed to reuse valid assessment
            )
            .one_or_none()
        )

        # If existing, check that user saw the current previous version
        if existing_assessment and presented_geneassessment_id != existing_assessment.id:
            raise ApiError(
                f"'presented_geneassessment_id': {presented_geneassessment_id} does not match latest existing geneassessment id: {existing_assessment.id}"
            )

        assessment_obj = GeneAssessment(
            gene_id=gene_id,
            user_id=user_id,
            usergroup_id=usergroup_id,
            evaluation=evaluation,
            genepanel_name=genepanel_name,
            genepanel_version=genepanel_version,
            analysis_id=analysis_id,
        )

        # If there's an existing assessment for this gene, we want to supercede it
        if existing_assessment:
            existing_assessment.date_superceeded = datetime.datetime.now(pytz.utc)
            assessment_obj.previous_assessment_id = existing_assessment.id

        log.debug(
            "Created assessment for gene id: %s, it supercedes: %s",
            assessment_obj.gene_id,
            assessment_obj.previous_assessment_id,
        )

        return assessment_obj
