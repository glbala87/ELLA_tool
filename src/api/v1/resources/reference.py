from vardb.datamodel import assessment

from api import schemas
from api.util.util import paginate, rest_filter, request_json


from util.pubmedxml import PubmedXmlParser

from api.v1.resource import Resource


class ReferenceListResource(Resource):

    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, num_per_page=100):
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
        Adds a reference to the database from pubmed xml input.
        Expected input:
        {
            'xml': <xml as string>
        }

        If it already exists, pretend it's inserted ok and
        return existing data instead. This is because it's
        a huge hassle to parse the xml in frontend to see check
        if it exists already.
        """
        ref_data = PubmedXmlParser().from_string(data['xml'].encode('utf-8'))

        reference = session.query(assessment.Reference).filter(
            assessment.Reference.pubmedID == ref_data['pubmedID']
        ).one_or_none()

        if not reference:
            ref_obj = assessment.Reference(
                **ref_data
            )
            session.add(ref_obj)
            session.commit()

            reference = session.query(assessment.Reference).filter(
                assessment.Reference.pubmedID == ref_data['pubmedID']
            ).one()

        return schemas.ReferenceSchema().dump(reference).data
