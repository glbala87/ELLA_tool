from vardb.datamodel import assessment

from api import schemas
from api.util.util import paginate, rest_filter, request_json, authenticate
from api.v1.resource import Resource
from api.util.allelereportcreator import AlleleReportCreator


class AlleleReportResource(Resource):

    @authenticate()
    def get(self, session, ar_id=None, user=None):
        """
        Returns a single allelereport.
        ---
        summary: Get allelereport
        tags:
          - AlleleReport
        parameters:
          - name: ar_id
            in: path
            type: integer
            description: AlleleReport id
        responses:
          200:
            schema:
                $ref: '#/definitions/AlleleReport'
            description: AlleleReport object
        """
        a = session.query(assessment.AlleleReport).filter(
            assessment.AlleleReport.id == ar_id
        ).one()
        result = schemas.AlleleReportSchema(strict=True).dump(a).data
        return result


class AlleleReportListResource(Resource):

    @authenticate()
    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, num_per_page=10000, user=None):
        """
        Returns a list of allelereports.

        * Supports `q=` filtering.
        * Supports pagination.
        ---
        summary: List allelereports
        tags:
          - AlleleReport
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
                $ref: '#/definitions/AlleleReport'
            description: List of allelereports
        """
        # TODO: Figure out how to deal with pagination
        return self.list_query(
            session,
            assessment.AlleleReport,
            schemas.AlleleReportSchema(strict=True),
            rest_filter=rest_filter,
            page=page,
            num_per_page=num_per_page
        )

    @authenticate()
    @request_json(
        [
            'allele_id',
            'evaluation',
        ],
        allowed=[
            # 'id' is excluded on purpose, as the endpoint should always result in a new report
            'analysis_id'
        ]
    )
    def post(self, session, data=None, user=None):
        """
        Creates a new AlleleReport(s) for a given allele(s).

        If any AlleleReport exists already for the same allele, it will be marked as superceded.

        **If report should be created as part of finalizing an analysis, check the analysis resource instead.**

        POST data example:
        ```javascript
        [
            {
                // New report will be created, superceding any old one
                "allele_id": 2,
                "evaluation": {...data...},
                "analysis_id": 3,  // Optional, should be given when report is made in context of analysis
                "presented_report_id": 6, # Could be None. The report displayed to the user.
                "alleleassessment_id": 3,  // Optional, should be given when report is made in context of an alleleassessment
            },
            {
                // Existing will be reused, so no report will be created...
                "reuse": true,
-               "presented_report_id": The report to reuse.
                ...
            }
        ]
        ```

        ---
        summary: Create allelereport
        tags:
          - AlleleReport
        parameters:
          - name: data
            in: body
            required: true
            schema:
              type: array
              items:
                title: AlleleReport data
                type: object
                required:
                  - allele_id
                  - evaluation
                properties:
                  presented_report_id:
                    description: Reuse exisisting object, no report will be created
                    type: integer
                  reuse:
                    description: If true, reuse exisisting object, se presented_report_id
                    type: boolean
                  analysis_id:
                    description: Analysis id
                    type: integer
                  allele_id:
                    description: Allele id
                    type: integer
                  alleleassessment_id:
                    description: AlleleAssessment id
                    type: integer
                  evaluation:
                    description: Evaluation data object
                    type: object

              example:
                - allele_id: 2
                  evaluation: {}
                  analysis_id: 3
                  alleleassessment_id: 3
                - presented_report_id: 3
                  reuse: true
            description: Submitted data
        responses:
          200:
            schema:
              type: array
              items:
                $ref: '#/definitions/AlleleReport'
            description: List of created alleleassessments
        """

        # if not isinstance(data, list):
        #     data = [data]

        # find assessments to link to the reports:
        assessment_ids = [d['alleleassessment_id'] for d in data if 'alleleassessment_id' in d]
        existing_assessments = session.query(assessment.AlleleAssessment).filter(
            assessment.AlleleAssessment.id.in_(assessment_ids)
        ).all()

        grouped_allelereports = AlleleReportCreator(session).create_from_data(
            user.id,
            data,
            alleleassessments=existing_assessments
        )

        created_allele_reports = grouped_allelereports['created']

        # if not isinstance(data, list):
        #     allele_reports_without_context = allele_reports_without_context[0]

        session.add_all(created_allele_reports)
        session.commit()

        return schemas.AlleleReportSchema().dump(created_allele_reports, many=True).data
