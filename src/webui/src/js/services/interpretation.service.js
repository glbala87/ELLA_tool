/* jshint esnext: true */

import {Service, Inject} from '../ng-decorators';
/**
 * Controller for dialog asking user whether to markreview or finalize interpretation.
 */
class ConfirmCompleteInterpretationController {

    constructor(modalInstance) {
        this.modal = modalInstance;
    }
}


@Service({
    serviceName: 'Interpretation'
})
@Inject('$rootScope',
        'Allele',
        'Analysis',
        'InterpretationResource',
        'User',
        '$uibModal',
        '$location')
class InterpretationService {

    constructor(rootScope,
        Allele,
        Analysis,
        interpretationResource,
        User,
        ModalService,
        LocationService) {


        //this._setWatchers(rootScope);
        this.analysisService = Analysis;
        this.alleleService = Allele;
        this.user = User;
        this.interpretationResource = interpretationResource;
        this.interpretation = null;
        this.modalService = ModalService;
        this.locationService = LocationService;
    }


    loadInterpretation(id) {
        if (id === undefined) {
            throw Error("You must provide an id");
        }
        return new Promise((resolve, reject) => {
            let userPromise = this.user.getCurrentUser();
            let interpretationPromise = this.interpretationResource.get(id);

            // Prepare interpretation and assign user
            Promise.all([userPromise, interpretationPromise]).spread((user, interpretation) => {
                interpretation.analysis.type = 'singlesample'; // TODO: remove me when implemented in backend
                console.log("Interpretation loaded", interpretation);
                resolve(interpretation);
            });
        });
    }

    /**
     * Saves the current state to server.
     * If the status is 'Not started',
     * we start the interpretation before saving.
     * @return {Promise} Promise that resolves upon completion.
     */
    save(interpretation) {
        if (interpretation.status === 'Not started') {
            interpretation.user_id = this.user.getCurrentUserId();
            return this.analysisService.start(
                interpretation.analysis.id,
            ).then(
                () => {
                    interpretation.status = 'Ongoing';
                    // Update on server in case user made any changes
                    // before starting analysis.
                    return this.save(interpretation);
                }
            );
        }
        else {
            return this.interpretationResource.updateState(interpretation).then(
                () => interpretation.setClean()
            );
        }
    }

    /**
     * Popups a confirmation dialog, asking to complete or finalize the interpretation
     * @param  {Interpretation} interpretation
     * @param  {Array(Allele)} alleles  Alleles to include allele/referenceassessments for.
     * @return {Promise}  Resolves upon completed submission.
     */
    confirmCompleteFinalize(interpretation, alleles) {
        let modal = this.modalService.open({
            templateUrl: 'ngtmpl/interpretationConfirmation.modal.ngtmpl.html',
            controller: ['$uibModalInstance', ConfirmCompleteInterpretationController],
            controllerAs: 'vm'
        });
        return modal.result.then(res => {
            // Save interpretation before marking as done
            if (res) {
                return this.save(interpretation).then(() => {
                    if (res === 'markreview') {
                        this.analysisService.markreview(interpretation.analysis.id);
                    }
                    else if (res === 'finalize') {

                        // Get all alleleassessments and referenceassessments used for this analysis.
                        let alleleassessments = [];
                        let referenceassessments = [];
                        for (let allele_state of interpretation.state.allele) {
                            // Only include assessments for alleles part of the supplied list.
                            // This is to avoid submitting assessments for alleles that have been
                            // removed from classification during interpretation process.
                            if (alleles.find(a => a.id === allele_state.allele_id)) {
                                alleleassessments.push(this.prepareAlleleAssessments(
                                    allele_state.allele_id,
                                    allele_state,
                                    interpretation.analysis.id
                                    ));
                                referenceassessments = referenceassessments.concat(this.prepareReferenceAssessments(
                                    allele_state,
                                    interpretation.analysis.id
                                ));
                            }
                        }
                        return this.analysisService.finalize(
                            interpretation.analysis.id,
                            alleleassessments,
                            referenceassessments
                        );
                    }
                    else {
                        throw `Got unknown option ${res} when confirming interpretation action.`;
                    }
                });
            }
            return true;
        });
    }

    prepareAlleleAssessments(allele_id, allelestate, analysis_id=null, genepanel_name=null, genepanel_version=null) {
        // If id is included, we're reusing an existing one.
        let aa = {
            allele_id: allele_id,

        };
        if (analysis_id) {
            aa.analysis_id = analysis_id;
        }
        if (genepanel_name &&
            genepanel_version) {
            aa.genepanel_name = genepanel_name;
            aa.genepanel_version = genepanel_version;
        }
        if ('id' in allelestate.alleleassessment) {
            aa.id = allelestate.alleleassessment.id;
        }
        else {
            // Fill in fields expected by backend
            Object.assign(aa, {
                user_id: this.user.getCurrentUserId(),
                classification: allelestate.alleleassessment.classification,
                evaluation: allelestate.alleleassessment.evaluation
            });
        }
        return aa;
    }

    prepareReferenceAssessments(allelestate, analysis_id=null, genepanel_name=null, genepanel_version=null) {
        let referenceassessments = [];
        if ('referenceassessments' in allelestate) {
            // Iterate over all referenceassessments for this allele
            for (let reference_state of allelestate.referenceassessments) {
                if (!reference_state.evaluation) {
                    continue;
                }
                let ra = {
                    reference_id: reference_state.reference_id,
                    allele_id: reference_state.allele_id
                }
                if (analysis_id) {
                    ra.analysis_id = analysis_id;
                }
                if (genepanel_name &&
                    genepanel_version) {
                    ra.genepanel_name = genepanel_name;
                    ra.genepanel_version = genepanel_version;
                }

                // If id is included, we're reusing an existing one.
                if ('id' in reference_state) {
                    ra.id = reference_state.id;
                }
                else {
                    // Fill in fields expected by backend
                    ra.evaluation = reference_state.evaluation || {};
                    ra.user_id = this.user.getCurrentUserId();
                }
                referenceassessments.push(ra);
            }
        }
        return referenceassessments;
    }

}


export default InterpretationService;
