import datetime

from vardb.datamodel import annotation

from api import schemas
from api.util.util import rest_filter, request_json

from api.v1.resource import Resource


class CustomAnnotationList(Resource):

    @rest_filter
    def get(self, session, rest_filter=None, page=None, num_per_page=None):
        return self.list_query(session,
                               annotation.CustomAnnotation,
                               schemas.CustomAnnotationSchema(),
                               rest_filter=rest_filter)

    @request_json(
        [
            'user_id',
            'allele_id',
            'annotations'
        ],
        True
    )
    def post(self, session, data=None):
        allele_id = data['allele_id']

        # Check for existing CustomAnnotations
        existing_ca = session.query(annotation.CustomAnnotation).filter(
            annotation.CustomAnnotation.allele_id == allele_id,
            annotation.CustomAnnotation.dateSuperceeded == None
        ).one_or_none()

        ca_data = {
            'user_id': data['user_id'],
            'annotations': data['annotations'],
            'allele_id': allele_id
        }

        if existing_ca:
            # Replace current
            ca_data['previousAnnotation_id'] = existing_ca.id
            existing_ca.dateSuperceeded = datetime.datetime.now()

        ca = annotation.CustomAnnotation(**ca_data)
        session.add(ca)
        session.commit()
        return schemas.CustomAnnotationSchema().dump(ca).data
