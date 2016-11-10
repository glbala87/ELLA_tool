from vardb.datamodel import assessment

from api import schemas
from api.util.util import paginate, rest_filter, request_json

from pubmed import PubMedParser

from api.v1.resource import Resource


class ReferenceListResource(Resource):

    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, num_per_page=100):
        """
        Returns a list of references.

        * Supports `q=` filtering.
        * Supports pagination.
        ---
        summary: List references
        tags:
          - Reference
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
                $ref: '#/definitions/Reference'
            description: List of references
        """
        return self.list_query(
            session,
            assessment.Reference,
            schemas.ReferenceSchema(strict=True),
            rest_filter=rest_filter,
            page=page,
            num_per_page=num_per_page
        )

    @request_json(['xml'], True)
    def post(self, session, data=None):
        """
        Creates a new Reference from the input [Pubmed](http://www.ncbi.nlm.nih.gov/pubmed) XML.

        For now, no feedback is given whether the reference already existed, a response code of is `200` is either case.
        If it already exists, it is not updated as the Pubmed data is assumed to be non-changing.

        ---
        summary: Create reference
        tags:
          - Reference
        parameters:
          - name: data
            in: body
            required: true
            schema:
              type: object
              required:
                - xml
              properties:
                xml:
                  description: Pubmed XML data
                  type: string
            description: Submitted data
        responses:
          200:
            schema:
              type: object
              $ref: '#/definitions/Reference'
            description: Created reference
        """

        ref_data = PubMedParser().from_xml_string(data['xml'].encode('utf-8'))

        reference = session.query(assessment.Reference).filter(
            assessment.Reference.pubmed_id == ref_data['pubmed_id']
        ).one_or_none()

        if not reference:
            ref_obj = assessment.Reference(
                **ref_data
            )
            session.add(ref_obj)
            session.commit()

            reference = session.query(assessment.Reference).filter(
                assessment.Reference.pubmed_id == ref_data['pubmed_id']
            ).one()

        return schemas.ReferenceSchema().dump(reference).data
