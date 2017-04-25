import datetime

from vardb.datamodel import assessment

from api import schemas
from api.util.util import paginate, rest_filter, request_json, authenticate

from api.v1.resource import Resource


class ReferenceAssessmentResource(Resource):

    @authenticate()
    def get(self, session, ra_id=None, user=None):
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
        a = session.query(assessment.ReferenceAssessment).filter(
            assessment.ReferenceAssessment.id == ra_id
        ).one()
        result = schemas.ReferenceAssessmentSchema(strict=True).dump(a).data
        return result


class ReferenceAssessmentListResource(Resource):

    @authenticate()
    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, num_per_page=None, user=None):
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
            num_per_page=100000  # FIXME: Fix proper pagination...
        )

    @authenticate()
    @request_json(
        [
            'allele_id',
            'reference_id',
            'evaluation',
            'genepanel_name',
            'genepanel_version',
            'analysis_id',
            'user_id'
        ],
        True
    )
    def post(self, session, data=None, user=None):
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

        obj = schemas.ReferenceAssessmentSchema(strict=True).load(data).data

        # If there exists an assessment already for this allele_id which is not yet curated,
        # we update that one instead.
        existing_ass = session.query(assessment.ReferenceAssessment).filter(
            assessment.ReferenceAssessment.allele_id == obj.allele_id,
            assessment.ReferenceAssessment.reference_id == obj.reference_id,
            assessment.ReferenceAssessment.date_superceeded == None,
            assessment.ReferenceAssessment.status == 0
        ).one_or_none()

        if existing_ass:
            obj.id = existing_ass.id
            session.merge(obj)
        else:
            session.add(obj)

        session.commit()

        # Reload to fetch all data
        new_obj = session.query(assessment.ReferenceAssessment).filter(
            assessment.ReferenceAssessment.id == obj.id
        ).one()
        return schemas.ReferenceAssessmentSchema(strict=True).dump(new_obj).data, 200


