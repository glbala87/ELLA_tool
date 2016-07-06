/* jshint esnext: true */

import {Service, Inject} from '../ng-decorators';


@Service({
    serviceName: 'Allele'
})
@Inject('User',
        'AlleleResource',
        'AlleleAssessmentResource',
        'ACMGClassificationResource',
        'ReferenceResource')
export class AlleleService {

    constructor(User,
                AlleleResource,
                AlleleAssessmentResource,
                ACMGClassificationResource,
                ReferenceResource) {
        this.user = User;
        this.alleleResource = AlleleResource;
        this.alleleAssessmentResource = AlleleAssessmentResource;
        this.acmgClassificationResource = ACMGClassificationResource;
        this.referenceResource = ReferenceResource;
    }

    getAlleles(allele_ids, sample_id=null, gp_name=null, gp_version=null) {
        return this.alleleResource.get(
            allele_ids,
            sample_id,
            gp_name,
            gp_version
        );
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
        return this.referenceResource.createOrUpdateReferenceAssessment(referenceassessment);
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
        return this.alleleAssessmentResource.createOrUpdateAlleleAssessment(alleleassessment);
    }

    /**
     * Updates the ACMG classifications for provided alleles.
     * referenceassessments is optional.
     */
    updateACMG(alleles, gp_name, gp_version, referenceassessments) {
        let allele_ids = alleles.map(a => a.id);
        return this.acmgClassificationResource.getByAlleleIds(
            allele_ids,
            gp_name,
            gp_version,
            referenceassessments
        ).then(res => {
            for (let [a_id, a_acmg] of Object.entries(res)) {
                // Assign result to related allele
                let allele = alleles.find(a => a.id.toString() === a_id);
                if (allele) {
                    allele.acmg = a_acmg;
                }
            }
        });
    }

    /**
     * Returns a string formatted for pasting into Alamut.
     * @param  {Allele} alleles List of alleles to include
     * @return {[type]}         String to paste into Alamut
     */
    formatAlamut(alleles) {

        // (Alamut also support dup, but we treat them as indels)
        // (dup: Chr13(GRCh37):g.32912008_3291212dup )

        let result = '';
        for (let allele of alleles) {
            result += `Chr${allele.chromosome}(${allele.genome_reference}):g.`;

            // Database is 0-based, alamut uses 1-based index
            let start = allele.start_position + 1;
            let end = allele.open_end_position + 1;

            if (allele.change_type === 'SNP') {
                // snp: Chr11(GRCh37):g.66285951C>Tdel:
                result += `${start}${allele.change_from}>${allele.change_to}\n`;
            }
            else if (allele.change_type === 'del') {
                // del: Chr13(GRCh37):g.32912008_32912011del
                result += `${start}_${end}del\n`;
            }
            else if (allele.change_type === 'ins') {
                // ins: Chr13(GRCh37):g.32912008_3291209insCGT
                result += `${start}_${start+1}ins${allele.change_to}\n`;
            }
            else if (allele.change_type === 'indel') {
                // delins: Chr13(GRCh37):g.32912008_32912011delinsGGG
                result += `${start}_${end}delins${allele.change_to}\n`;
            }
            else {
                // edge case, shouldn't happen, but this is valid format as well
                result += `${start}\n`;
            }

        }
        return result;
    }
}
