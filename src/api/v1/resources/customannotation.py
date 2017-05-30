import datetime
import pytz
from vardb.datamodel import annotation

from api import schemas
from api.util.util import rest_filter, request_json, authenticate

from api.v1.resource import LogRequestResource


class CustomAnnotationList(LogRequestResource):

    @authenticate()
    @rest_filter
    def get(self, session, rest_filter=None, page=None, num_per_page=None, user=None):
        """
        Returns a list of customannotations.

        * Supports `q=` filtering.
        * Supports pagination.
        ---
        summary: List customannotations
        tags:
          - Annotation
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
                $ref: '#/definitions/CustomAnnotation'
            description: List of customannotations
        """
        return self.list_query(session,
                               annotation.CustomAnnotation,
                               schemas.CustomAnnotationSchema(),
                               rest_filter=rest_filter)

    @authenticate()
    @request_json(
        [
            'allele_id',
            'annotations'
        ],
        True
    )
    def post(self, session, data=None, user=None):
        """
        Creates new CustomAnnotation(s) for a given allele id(s).

        The new CustomAnnotation object will act as current CustomAnnotation for this
        allele, and the old one is archived.
        The old can be accessed via the `previous_annotation_id` field.

        ---
        summary: Create customannotation
        tags:
          - Annotation
        parameters:
          - name: data
            in: body
            required: true
            schema:
              title: CustomAnnotation data
              type: object
              required:
                - allele_id
                - annotations
              properties:
                allele_id:
                  description: Allele id
                  type: integer
                annotations:
                  description: Annotation data object
                  type: object
            description: Submitted data
        responses:
          200:
            schema:
              $ref: '#/definitions/CustomAnnotation'
            description: Created customannotation
        """
        allele_id = data['allele_id']

        # Check for existing CustomAnnotations
        existing_ca = session.query(annotation.CustomAnnotation).filter(
            annotation.CustomAnnotation.allele_id == allele_id,
            annotation.CustomAnnotation.date_superceeded == None
        ).one_or_none()

        ca_data = {
            'user_id': user.id,
            'annotations': data['annotations'],
            'allele_id': allele_id
        }

        if existing_ca:
            # Replace current
            ca_data['previous_annotation_id'] = existing_ca.id
            existing_ca.date_superceeded = datetime.datetime.now(pytz.utc)

        ca = annotation.CustomAnnotation(**ca_data)
        session.add(ca)
        session.commit()
        return schemas.CustomAnnotationSchema().dump(ca).data
