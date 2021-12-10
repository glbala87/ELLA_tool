from typing import Dict, Optional
from api import schemas
from api.schemas.pydantic.v1 import validate_output
from api.schemas.pydantic.v1.resources import (
    ReferenceAssessmentListResponse,
    ReferenceAssessmentPostRequest,
    ReferenceAssessmentResponse,
)
from api.util.util import authenticate, paginate, request_json, rest_filter
from api.v1.resource import LogRequestResource
from sqlalchemy.orm import Session
from vardb.datamodel import assessment, user


class ReferenceAssessmentResource(LogRequestResource):
    @authenticate()
    @validate_output(ReferenceAssessmentResponse)
    def get(self, session: Session, ra_id: int, user: user.User):
        """
        Returns a single referenceassessment.
        ---
        summary: Get referenceassessment
        tags:
          - ReferenceAssessment
        parameters:
          - name: ra_id
            in: path
            type: integer
            description: ReferenceAssessment id
        responses:
          200:
            schema:
                $ref: '#/definitions/ReferenceAssessment'
            description: ReferenceAssessment object
        """
        a = (
            session.query(assessment.ReferenceAssessment)
            .filter(assessment.ReferenceAssessment.id == ra_id)
            .one()
        )
        result = schemas.ReferenceAssessmentSchema(strict=True).dump(a).data
        return result


class ReferenceAssessmentListResource(LogRequestResource):
    @authenticate()
    @validate_output(ReferenceAssessmentListResponse, paginated=True)
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
        Returns a list of referenceassessment.

        * Supports `q=` filtering.
        * Supports pagination.
        ---
        summary: List referenceassessment
        tags:
          - ReferenceAssessment
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
                $ref: '#/definitions/ReferenceAssessment'
            description: List of referenceassessment
        """
        return self.list_query(
            session,
            assessment.ReferenceAssessment,
            schemas.ReferenceAssessmentSchema(strict=True),
            rest_filter=rest_filter,
            page=page,
            per_page=100000,  # FIXME: Fix proper pagination...
        )

    @authenticate()
    @validate_output(ReferenceAssessmentResponse)
    @request_json(model=ReferenceAssessmentPostRequest)
    def post(self, session: Session, data: ReferenceAssessmentPostRequest, user: user.User):
        """
        Creates a new ReferenceAssessment(s) for a given allele(s).

        If any ReferenceAssessment exists already for the same allele, it will be marked as superceded.

        **If assessment should be created as part of finalizing an analysis, check the `analyses/{id}/finalize` resource instead.**

        POST data example:
        ```
        {
            # New assessment will be created, superceding any old one
            "user_id": 1,
            "allele_id": 2,
            "evaluation": {...data...},
            "analysis_id": 3,  # Optional, should be given when assessment is made in context of analysis
            "genepanel_name": "HBOC",
            "genepanel_version": "v01"
        }
        ```

        ---
        summary: Create referenceassessment
        tags:
          - ReferenceAssessment
        parameters:
          - name: data
            in: body
            required: true
            schema:
              type: array
              items:
                title: ReferenceAssessment data
                type: object
                required:
                  - user_id
                  - allele_id
                  - genepanel_name
                  - genepanel_version
                  - evaluation
                  - analysis_id
                properties:
                  user_id:
                    description: User id
                    type: integer
                  analysis_id:
                    description: Analysis id
                    type: integer
                  genepanel_name:
                    description: Genepanel name. Required if no analysis id
                    type: string
                  genepanel_version:
                    description: Genepanel version. Required if no analysis id
                    type: string
                  allele_id:
                    description: Allele id
                    type: integer
                  evaluation:
                    description: Evaluation data object
                    type: object
            description: Submitted data
        responses:
          200:
            schema:
              $ref: '#/definitions/ReferenceAssessment'
            description: Created referenceassessment
        """

        # If there exists an assessment already for this allele_id which is not yet curated,
        # we update that one instead.
        existing_ass = (
            session.query(assessment.ReferenceAssessment)
            .filter(
                assessment.ReferenceAssessment.allele_id == data.allele_id,
                assessment.ReferenceAssessment.reference_id == data.reference_id,
                assessment.ReferenceAssessment.date_superceeded.is_(None),
                assessment.ReferenceAssessment.status == 0,
            )
            .one_or_none()
        )

        if existing_ass:
            data.id = existing_ass.id
            session.merge(data)
        else:
            session.add(data)

        session.commit()

        # Reload to fetch all data
        new_obj = (
            session.query(assessment.ReferenceAssessment)
            .filter(assessment.ReferenceAssessment.id == data.id)
            .one()
        )
        return schemas.ReferenceAssessmentSchema(strict=True).dump(new_obj).data
