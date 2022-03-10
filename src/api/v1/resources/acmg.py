from typing import Dict, List
from api.schemas.pydantic.v1 import validate_output
from api.schemas.pydantic.v1.resources import (
    ACMGAlleleRequest,
    ACMGAlleleResponse,
    ACMGClassificationResponse,
)
from api.util.util import authenticate, request_json
from api.v1.resource import LogRequestResource
from datalayer import ACMGDataLoader
from flask import request
from sqlalchemy import cast
from sqlalchemy.dialects.postgresql import ARRAY, array
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import func
from sqlalchemy.types import Integer
from vardb.datamodel import allele, gene, user


class ACMGAlleleResource(LogRequestResource):
    def get_alleles(self, session: Session, allele_ids: List[int]):
        """

        :param session:
        :param allele_ids:
        :return: alleles
        :rtype: allele.Allele
        """
        if allele_ids:
            return (
                session.query(allele.Allele)
                .filter(
                    allele.Allele.id.in_(
                        session.query(
                            func.unnest(cast(array(allele_ids), ARRAY(Integer)))
                        ).subquery()
                    )
                )
                .all()
            )
        else:
            return []

    def get_genepanel(self, session: Session, gp_name: str, gp_version: str):
        """
        Look up a genepanel

        :param session:
        :param gp_name:
        :type gp_name: str
        :param gp_version:
        :type gp_version: str
        :return: gene panel
        :rtype:  vardb.datamodel.gene.Genepanel
        """
        return (
            session.query(gene.Genepanel)
            .filter(gene.Genepanel.name == gp_name, gene.Genepanel.version == gp_version)
            .one()
        )

    @authenticate(user_config=True)
    @validate_output(ACMGAlleleResponse)
    @request_json(model=ACMGAlleleRequest)
    def post(self, session: Session, data: ACMGAlleleRequest, user: user.User, user_config: Dict):
        """
        Returns calculated ACMG codes for provided alleles and related data.

        Input data should look like this:

        ```javascript
        {
            "referenceassessments": [ // Optional
                {
                    "allele_id": 2,
                    "reference_id": 4,
                    "evaluation": {...}
                },
                ...
            ],
            "allele_ids": [1, 2, 3, 4],
            "gp_name": "PanelName",
            "gp_version": "v01"
        }
        ```

        ---
        summary: Get ACMG codes
        tags:
          - ACMG
        parameters:
          - name: data
            in: body
            type: object
            required: true
            schema:
              title: Data object
              type: object
              properties:
                referenceassessments:
                  name: referenceassessment
                  type: array
                  items:
                    title: ReferenceAssessment
                    type: object
                    required:
                      - allele_id
                      - reference_id
                      - evaluation
                    properties:
                      allele_id:
                        description: Allele id
                        type: integer
                      reference_id:
                        description: Reference id
                        type: integer
                      evaluation:
                        description: Evaluation data object
                        type: object
                allele_ids:
                  name: Allele ids
                  type: array
                  items:
                    type: integer
                gp_name:
                  name: Genepanel name
                  type: string
                  description: Required if allele_ids is provided
                gp_version:
                  name: Genepanel version
                  type: string
                  description: Required if allele_ids is provided
        responses:
          200:
            schema:
              type: object
              required:
                - "{allele_id}"
              properties:
                "{allele_id}":
                  type: array
                  items:
                    title: Codes
                    type: object
                    required:
                      - source
                      - code
                      - match
                      - value
                    properties:
                      source:
                        type: string
                        description: Source contributing to code
                      code:
                        type: string
                        description: Code
                      match:
                        type: array
                        description: Parameter contributing to the match
                        items:
                          type: string
                      value:
                        description: Value that matched
                        type: array
                        items:
                          type: string
                      op:
                        description: Comparison operator used
                        type: string
              example:
                '7':
                  codes:
                    - source: genepanel.inheritance
                      code: REQ_GP_AD
                      match:
                        - AD
                      value:
                        - AD
                      op: "$in"
                    - source: transcript.Consequence
                      code: REQ_no_aa_change
                      match:
                        - synonymous_variant
                      value:
                        - stop_retained_variant
                        - 5_prime_UTR_variant
                        - 3_prime_UTR_variant
            description: List of alleleassessments
        """

        # This is POST by design, which is not strictly RESTful, but we
        # need a lot of dynamic user data and it works well.
        alleles = self.get_alleles(session, data.allele_ids)
        genepanel = self.get_genepanel(session, data.gp_name, data.gp_version)

        return ACMGDataLoader(session).from_objs(
            alleles, data.referenceassessments, genepanel, user_config["acmg"]
        )


class ACMGClassificationResource(LogRequestResource):
    @validate_output(ACMGClassificationResponse)
    def get(self, session: Session):
        """
        Returns the calculated suggested classification given the provided codes.
        ---
        summary: Get suggested classification
        tags:
          - ACMG
        parameters:
          - name: codes
            in: query
            type: string
            description: Comma separated list of codes.
        responses:
          200:
            schema:
              title: Classification
              type: object
              required:
                - classification
                - contributors
                - meta
                - message
                - class
              properties:
                classification:
                  type: string
                contributors:
                  type: array
                  items:
                    type: string
                meta:
                  type: object
                message:
                  type: string
                class:
                  type: string
              example:
                classification: Pathogenic
                contributors:
                  - PVS1
                  - PSxPM1
                meta: {}
                message: Pathogenic
                class: 5


            description: List of alleles
        """
        codes_raw = request.args.get("codes")
        if not codes_raw:
            raise RuntimeError("Missing required field 'codes'")
        codes = codes_raw.split(",")

        return ACMGDataLoader(session).get_classification(codes)
