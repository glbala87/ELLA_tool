from flask import request
from vardb.datamodel import allele, gene
from datalayer import ACMGDataLoader
from api.util.util import request_json, authenticate
from api.v1.resource import LogRequestResource


class ACMGAlleleResource(LogRequestResource):
    def get_alleles(self, session, allele_ids):
        """

        :param session:
        :param allele_ids:
        :return: alleles
        :rtype: allele.Allele
        """
        if allele_ids:
            return session.query(allele.Allele).filter(allele.Allele.id.in_(allele_ids)).all()
        else:
            return []

    def get_genepanel(self, session, gp_name, gp_version):
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
    @request_json(["allele_ids", "gp_name", "gp_version"], allowed=["referenceassessments"])
    def post(self, session, data=None, user=None, user_config=None):
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
        alleles = self.get_alleles(session, data["allele_ids"])
        genepanel = self.get_genepanel(session, data["gp_name"], data["gp_version"])

        return ACMGDataLoader(session).from_objs(
            alleles, data.get("referenceassessments"), genepanel, user_config["acmg"]
        )


class ACMGClassificationResource(LogRequestResource):
    def get(self, session):
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
