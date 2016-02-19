from flask import request
from vardb.datamodel import assessment, allele, gene

from api import ApiError

from api.util.acmgdataloader import ACMGDataLoader

from api.v1.resource import Resource


class ACMGClassificationResource(Resource):

    def get_alleles(self, session, allele_ids):
        if allele_ids:
            return session.query(allele.Allele).filter(
                allele.Allele.id.in_(allele_ids)
            ).all()
        else:
            return []

    def get_ref_assessments(self, session, ra_ids):
        if ra_ids:
            return session.query(assessment.ReferenceAssessment).filter(
                assessment.ReferenceAssessment.id.in_(ra_ids)
            ).all()
        else:
            return []

    def get_ref_assessments_allele_ids(self, session, allele_ids):
        return session.query(assessment.ReferenceAssessment).filter(
            assessment.ReferenceAssessment.allele_id.in_(allele_ids),
            assessment.ReferenceAssessment.dateSuperceeded == None
        ).all()

    def get_genepanel(self, session, gp_name, gp_version):
        return session.query(gene.Genepanel).filter(
            gene.Genepanel.name == gp_name,
            gene.Genepanel.version == gp_version
        ).one()

    def get(self, session):
        allele_ids = []
        if request.args.get("allele_ids"):
            allele_ids = [int(a) for a in request.args.get("allele_ids").split(",")]
        if not allele_ids:
            raise ApiError("Missing required argument 'allele_ids'")
        reference_assessment_ids = []
        if request.args.get("reference_assessment_ids"):
            ra_ids = request.args.get("reference_assessment_ids").split(",")
            reference_assessments = self.get_ref_assessments(session, ra_ids)
        else:
            reference_assessments = self.get_ref_assessments_allele_ids(session, allele_ids)

        alleles = self.get_alleles(session, allele_ids)
        gp_name = request.args.get("gp_name")
        gp_version = request.args.get("gp_version")

        reference_assessments = self.get_ref_assessments(session, reference_assessment_ids)
        genepanel = self.get_genepanel(session, gp_name, gp_version)

        return ACMGDataLoader(session).from_objs(
            alleles,
            reference_assessments,
            genepanel
        )
