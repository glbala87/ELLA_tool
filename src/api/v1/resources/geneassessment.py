from vardb.datamodel import assessment

from api import schemas
from api.util.util import paginate, rest_filter, authenticate, request_json
from api.v1.resource import LogRequestResource
from datalayer import GeneAssessmentCreator


class GeneAssessmentResource(LogRequestResource):
    @authenticate()
    def get(self, session, ga_id=None, user=None):
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
    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, per_page=10000, user=None):
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
    @request_json(jsonschema="geneAssessmentPost.json")
    def post(self, session, data=None, user=None):
        ga = GeneAssessmentCreator(session)
        created = ga.create_from_data(
            user.id,
            user.group_id,
            data["gene_id"],
            data["genepanel_name"],
            data["genepanel_version"],
            data["evaluation"],
            data.get("presented_geneassessment_id"),
            data.get("analysis_id"),
        )

        session.add(created)
        session.commit()
        return schemas.GeneAssessmentSchema().dump(created).data
