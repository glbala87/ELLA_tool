from flask import request
from vardb.datamodel import assessment, allele, gene

from api import ApiError

from util.acmgdataloader import ACMGDataLoader

from api.v1.resource import Resource


class ACMGClassificationResource(Resource):

    def get_alleles(self, session, allele_ids):
        if allele_ids:
            return session.query(allele.Allele).filter(
                allele.Allele.id.in_(allele_ids)
            ).all()
        else:
            return []

    def get_reference_assessments(self, session, ra_ids):
        if ra_ids:
            return session.query(assessment.ReferenceAssessment).filter(
                assessment.ReferenceAssessment.id.in_(ra_ids)
            ).all()
        else:
            return []

    def get_genepanel(self, session, gp_name, gp_version):
        return session.query(gene.Genepanel).filter(
            gene.Genepanel.name == gp_name,
            gene.Genepanel.version == gp_version
        ).one()

    def get(self, session):
        allele_ids = []
        if request.args.get("allele_ids"):
            allele_ids = request.args.get("allele_ids").split(",")
        if not allele_ids:
            raise ApiError("Missing required argument 'allele_ids'")
        reference_assesment_ids = []
        if request.args.get("reference_assessment_ids"):
            reference_assesment_ids = request.args.get("reference_assessment_ids").split(",")
        gp_name = request.args.get("gp_name")
        gp_version = request.args.get("gp_version")

        alleles = self.get_alleles(session, allele_ids)
        reference_assessments = self.get_reference_assessments(session, reference_assesment_ids)
        genepanel = self.get_genepanel(session, gp_name, gp_version)

        return ACMGDataLoader(session).from_objs(
            alleles,
            reference_assessments,
            genepanel
        )
