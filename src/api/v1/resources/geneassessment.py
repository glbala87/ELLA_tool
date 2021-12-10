from typing import Dict, Optional
from api import schemas
from api.schemas.pydantic.v1 import validate_output
from api.schemas.pydantic.v1.resources import (
    GeneAssessmentListResponse,
    GeneAssessmentPostRequest,
    GeneAssessmentResponse,
)
from api.util.util import authenticate, paginate, request_json, rest_filter
from api.v1.resource import LogRequestResource
from datalayer import GeneAssessmentCreator
from sqlalchemy.orm import Session
from vardb.datamodel import assessment, user


class GeneAssessmentResource(LogRequestResource):
    @authenticate()
    @validate_output(GeneAssessmentResponse)
    def get(self, session: Session, ga_id: int, user: user.User):
        """
        Returns a single geneassessment.
        ---
        summary: Get geneassessment
        tags:
          - GeneAssessment
        parameters:
          - name: ga_id
            in: path
            type: integer
            description: GeneAssessment id
        responses:
          200:
            schema:
                $ref: '#/definitions/GeneAssessment'
            description: GeneAssessment object
        """
        a = (
            session.query(assessment.GeneAssessment)
            .filter(assessment.GeneAssessment.id == ga_id)
            .one()
        )
        result = schemas.GeneAssessmentSchema(strict=True).dump(a).data
        return result


class GeneAssessmentListResource(LogRequestResource):
    @authenticate()
    @validate_output(GeneAssessmentListResponse, paginated=True)
    @paginate
    @rest_filter
    def get(
        self,
        session: Session,
        rest_filter: Optional[Dict],
        page: int,
        per_page: int,
        user: user.User,
    ):
        """
        Returns a list of geneassessments.

        * Supports `q=` filtering.
        * Supports pagination.
        ---
        summary: List geneassessments
        tags:
          - GeneAssessment
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
                $ref: '#/definitions/GeneAssessment'
            description: List of geneassessments
        """
        # TODO: Figure out how to deal with pagination
        return self.list_query(
            session,
            assessment.GeneAssessment,
            schemas.GeneAssessmentSchema(strict=True),
            rest_filter=rest_filter,
            page=page,
            per_page=per_page,
        )

    @authenticate()
    @validate_output(GeneAssessmentResponse)
    @request_json(model=GeneAssessmentPostRequest)
    def post(self, session: Session, data: GeneAssessmentPostRequest, user: user.User):
        ga = GeneAssessmentCreator(session)
        created = ga.create_from_data(
            user.id,
            user.group_id,
            data.gene_id,
            data.genepanel_name,
            data.genepanel_version,
            data.evaluation.dump(),
            data.presented_geneassessment_id,
            data.analysis_id,
        )

        session.add(created)
        session.commit()
        return schemas.GeneAssessmentSchema().dump(created).data
