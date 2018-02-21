/* jshint esnext: true */

import { Service, Inject } from '../ng-decorators'

@Service({
    serviceName: 'Allele'
})
@Inject(
    'User',
    'AlleleResource',
    'AlleleAssessmentResource',
    'ACMGClassificationResource',
    'ReferenceResource'
)
export class AlleleService {
    constructor(
        User,
        AlleleResource,
        AlleleAssessmentResource,
        ACMGClassificationResource,
        ReferenceResource
    ) {
        this.user = User
        this.alleleResource = AlleleResource
        this.alleleAssessmentResource = AlleleAssessmentResource
        this.acmgClassificationResource = ACMGClassificationResource
        this.referenceResource = ReferenceResource
    }

    getAlleles(
        allele_ids,
        sample_id = null,
        gp_name = null,
        gp_version = null,
        related_entities = null
    ) {
        return this.alleleResource.get(allele_ids, sample_id, gp_name, gp_version, related_entities)
    }

    getAllelesByQuery(
        query,
        sample_id = null,
        gp_name = null,
        gp_version = null,
        related_entities = null
    ) {
        return this.alleleResource.getByQuery(
            query,
            sample_id,
            gp_name,
            gp_version,
            related_entities
        )
    }

    /**
     * POSTs an referenceassessment to the backend.
     * Note! Normally you want to use the analysis' finalize
     * action, and provide the referenceassessments there.
     * Only use this method when you have a single referenceassessment
     * that is not submitted as part of the interpretation workflow.
     * @param  {Object} referenceassessment Data as returned from prepareReferenceAssessment()
     * @return {Promise}                    Promise resolved with response from backend.
     */
    submitReferenceAssessment(referenceassessment) {
        return this.referenceResource.createOrUpdateReferenceAssessment(referenceassessment)
    }

    /**
     * POSTs an alleleassessment to the backend.
     * Note! Normally you want to use the analysis' finalize
     * action, and provide the alleleassessments there.
     * Only use this method when you have a single alleleassessment
     * that is not submitted as part of the interpretation workflow.
     * @param  {Object} alleleassessment Data as returned from prepareAlleleAssessment()
     * @return {Promise}                 Promise resolved with response from backend.
     */
    submitAlleleAssessment(alleleassessment) {
        return this.alleleAssessmentResource.createOrUpdateAlleleAssessment(alleleassessment)
    }

    /**
     * POSTs an allelereport to the backend.
     * Note! Normally you want to use the analysis' finalize
     * action, and provide the allelereport there.
     * Only use this method when you have a single allelereport
     * that is not submitted as part of the interpretation workflow.
     * @param  {Object} allelereport Data as returned from prepareAlleleReport()
     * @return {Promise}             Promise resolved with response from backend.
     */
    submitAlleleReport(allelereport) {
        return this.alleleAssessmentResource.createOrUpdateAlleleReport(allelereport)
    }

    /**
     * Updates the ACMG classifications for provided alleles.
     * referenceassessments is optional.
     */
    updateACMG(alleles, gp_name, gp_version, referenceassessments) {
        let allele_ids = alleles.map(a => a.id)
        return this.acmgClassificationResource
            .getByAlleleIds(allele_ids, gp_name, gp_version, referenceassessments)
            .then(res => {
                for (let [a_id, a_acmg] of Object.entries(res)) {
                    // Assign result to related allele
                    let allele = alleles.find(a => a.id.toString() === a_id)
                    if (allele) {
                        allele.acmg = a_acmg
                    }
                }
            })
    }
}
