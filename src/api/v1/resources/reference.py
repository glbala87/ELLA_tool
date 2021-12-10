from typing import Dict, Optional
from api import schemas
from api.schemas.pydantic.v1 import validate_output
from api.schemas.pydantic.v1.common import SearchFilter
from api.schemas.pydantic.v1.resources import (
    ReferenceListRequest,
    ReferenceListResponse,
    ReferencePostResponse,
)
from api.util.util import authenticate, paginate, request_json, rest_filter, search_filter
from api.v1.resource import LogRequestResource
from pubmed import PubMedParser
from sqlalchemy.orm import Session
from vardb.datamodel import assessment, user


class ReferenceListResource(LogRequestResource):
    @authenticate()
    @validate_output(ReferenceListResponse, paginated=True)
    @paginate
    @rest_filter
    @search_filter
    def get(
        self,
        session: Session,
        rest_filter: Optional[Dict],
        search_filter: Optional[SearchFilter],
        page: int,
        per_page: int,
        user: user.User,
    ):
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

        if search_filter is not None:
            assert rest_filter is None
            return self.list_search(
                session,
                assessment.Reference,
                search_filter=search_filter,
                schema=schemas.ReferenceSchema(strict=True),
                page=page,
                per_page=per_page,
            )
        else:
            return self.list_query(
                session,
                assessment.Reference,
                schemas.ReferenceSchema(strict=True),
                rest_filter=rest_filter,
                page=page,
                per_page=per_page,
            )

    @authenticate()
    @validate_output(ReferencePostResponse)
    @request_json(model=ReferenceListRequest)
    def post(self, session: Session, data: ReferenceListRequest, user: user.User):
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
        if data.pubmedData is not None:
            ref_data = PubMedParser().parse(data.pubmedData)

            reference = (
                session.query(assessment.Reference)
                .filter(assessment.Reference.pubmed_id == ref_data["pubmed_id"])
                .one_or_none()
            )

            if not reference:
                ref_obj = assessment.Reference(**ref_data)
                session.add(ref_obj)
                session.commit()

                reference = (
                    session.query(assessment.Reference)
                    .filter(assessment.Reference.pubmed_id == ref_data["pubmed_id"])
                    .one()
                )

            return schemas.ReferenceSchema().dump(reference).data
        elif data.manual is not None:
            reference = (
                session.query(assessment.Reference)
                .filter(
                    *[getattr(assessment.Reference, k) == v for k, v in list(data.manual.items())]
                )
                .first()
            )
            if reference is not None:
                return schemas.ReferenceSchema().dump(reference).data

            ref_obj = assessment.Reference(**data.manual)

            session.add(ref_obj)
            session.commit()

            reference = (
                session.query(assessment.Reference)
                .filter(
                    *[getattr(assessment.Reference, k) == v for k, v in list(data.manual.items())]
                )
                .one()
            )

            return schemas.ReferenceSchema().dump(reference).data
