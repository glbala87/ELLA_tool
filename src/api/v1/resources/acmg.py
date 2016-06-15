from flask import request
from vardb.datamodel import assessment, allele, gene

from api import ApiError

from api.util.acmgdataloader import ACMGDataLoader
from api.util.util import request_json

from api.v1.resource import Resource


class ACMGAlleleResource(Resource):

    def get_alleles(self, session, allele_ids):
        """

        :param session:
        :param allele_ids:
        :return: alleles
        :rtype: allele.Allele
        """
        if allele_ids:
            return session.query(allele.Allele).filter(
                allele.Allele.id.in_(allele_ids)
            ).all()
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
        return session.query(gene.Genepanel).filter(
            gene.Genepanel.name == gp_name,
            gene.Genepanel.version == gp_version
        ).one()


    @request_json(
        None,
        allowed=[
            'allele_ids',
            'referenceassessments',
            'gp_name',
            'gp_version',
            'analysis_id'
        ]
    )
    def post(self, session, data=None):
        """
        Calculates ACMG codes for the provided data.

        Input data should look like this:

        {
            "referenceassessments": [
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

        If 'allele_ids' is provided, you must also pass in 'gp_name' and 'gp_version'.

        :note: This is POST by design, which is not strictly RESTful, but we
        need a lot of dynamic user data and it works well.
        """


        alleles = None
        genepanel = None
        if 'allele_ids' in data:
            alleles = self.get_alleles(session, data['allele_ids'])
            if 'gp_name' in data and 'gp_version' in data:
                genepanel = self.get_genepanel(session, data['gp_name'], data['gp_version'])
            else:
                raise ApiError("You need to provide both 'gp_name' and 'gp_version' when 'allele_ids' is given")

        return ACMGDataLoader(session).from_objs(
            alleles,
            data.get('referenceassessments'),
            genepanel
        )


class ACMGClassificationResource(Resource):

    def get(self, session):
        codes_raw = request.args.get('codes')
        if not codes_raw:
            raise RuntimeError("Missing required field 'codes'")
        codes = codes_raw.split(',')

        return ACMGDataLoader(session).get_classification(codes)
