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

    getAllelesByAnalysis(allele_ids, analysis) {
        return this.getAlleles(
            allele_ids,
            analysis.samples[0].id, // TODO: Handle multiple samples
            analysis.genepanel.name,
            analysis.genepanel.version
        )
    }

    createOrUpdateReferenceAssessment(data, allele, reference, gp_name=null, gp_version=null, analysis_id=null) {

        // Make copy and add/update mandatory fields before submission
        let copy_ra = Object.assign({}, data);

        return this.user.getCurrentUser().then(user => {
            Object.assign(copy_ra, {
                allele_id: allele.id,
                reference_id: reference.id,
                genepanelName: gp_name,
                genepanelVersion: gp_version,
                analysis_id: analysis_id,
                status: 0,  // Status is set to 0. Finalization happens in another step.
                user_id: user.id
            });

            // We set 'evaluation' again to ensure frontend is synced with server.
            // Then we update the interpretation state on the server, in order to make sure everything is in sync.
            return this.referenceResource.createOrUpdateReferenceAssessment(copy_ra).then(updated_ra => {
                data.id = updated_ra.id;
                data.evaluation = updated_ra.evaluation;
                data.analysis_id = updated_ra.analysis_id;
                return data;
            });
        });
    }

    createOrUpdateAlleleAssessment(data, allele, gp_name=null, gp_version=null, analysis_id=null) {

        // Make copy and add mandatory fields before submission
        let copy_aa = Object.assign({}, data);
        delete copy_aa.user;  // Remove extra data
        delete copy_aa.secondsSinceUpdate;
        // TODO: Add transcript
        return this.user.getCurrentUser().then(user => {
            Object.assign(copy_aa, {
                allele_id: allele.id,
                annotation_id: allele.annotation.annotation_id,
                genepanelName: gp_name,
                genepanelVersion: gp_version,
                analysis_id: analysis_id,
                user_id: user.id
            });

            // Update the data with the response to include the updated fields into relevant alleleassessment
            // We set 'evaluation' and 'classification' again to ensure frontend is synced with server.

            return this.alleleAssessmentResource.createOrUpdateAlleleAssessment(copy_aa).then(aa => {
                data.id = aa.id;
                data.classification = aa.classification;
                data.evaluation = aa.evaluation;
                data.analysis_id = aa.analysis_id;
                data.status = aa.status;
                return data;
            });

        });

    }

    /**
     * Updates the ACMG classifications for all alleles.
     * To do this we need gather all the allele ids.
     */
    updateACMG(alleles, gp_name, gp_version) {
        let allele_ids = alleles.map(a => a.id);
        return this.acmgClassificationResource.getByAlleleIds(
            allele_ids,
            gp_name,
            gp_version
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
}
