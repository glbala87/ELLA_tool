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
            let puser = this.user.getCurrentUser();
            let pint = this.interpretationResource.get(id);

            // Prepare interpretation and assign user
            Promise.all([puser, pint]).spread((user, interpretation) => {
                interpretation.analysis.type = 'singlesample'; // TODO: remove me when implemented in backend
            });

            // Resolve final promise
            Promise.all([puser, pint]).spread((user, interpretation) => {
                return this.reloadAlleles(interpretation).then(alleles => {
                    console.log("Interpretation loaded", interpretation);
                    resolve(interpretation);
                });
            });
        });
    }

    reloadAlleles(interpretation) {
        return this.alleleService.getAlleles(
            interpretation.allele_ids,
            interpretation.analysis.samples[0].id,
            interpretation.analysis.genepanel.name,
            interpretation.analysis.genepanel.version
        ).then(alleles => {
            interpretation.setAlleles(alleles);
            return alleles;
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
     */
    confirmCompleteFinalize(interpretation) {
        let modal = this.modalService.open({
            templateUrl: 'ngtmpl/interpretationConfirmation.modal.ngtmpl.html',
            controller: ['$uibModalInstance', ConfirmCompleteInterpretationController],
            controllerAs: 'vm'
        });
        return modal.result.then(res => {
            // Save interpretation before marking as done
            if (res) {
                this.save(interpretation).then(() => {
                    if (res === 'markreview') {
                        this.analysisService.markreview(interpretation.analysis.id);
                    }
                    else if (res === 'finalize') {

                        // Get all alleleassessments and referenceassessments used for this analysis.
                        let alleleassessments = [];
                        let referenceassessments = [];
                        for (let [allele_id, allele_state] of Object.entries(interpretation.state.allele)) {
                            alleleassessments.push(this.prepareAlleleAssessmentsFromAlleleState(
                                parseInt(allele_id),
                                interpretation.analysis.id,
                                allele_state
                                ));
                            referenceassessments += this.prepareReferenceAssessmentsFromAlleleState(
                                parseInt(allele_id),
                                interpretation.analysis.id,
                                allele_state
                            );
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

    prepareAlleleAssessmentsFromAlleleState(allele_id, analysis_id, allelestate) {
        // If id is included, we're reusing an existing one.
        if ('id' in allelestate.alleleassessment) {
            return {
                allele_id: allele_id,
                id: allelestate.alleleassessment.id,
                analysis_id: analysis_id
            };
        }
        else {
            // Fill in fields expected by backend
            return {
                allele_id: allele_id,
                analysis_id: analysis_id,
                user_id: this.user.getCurrentUserId(),
                classification: allelestate.alleleassessment.classification,
                evaluation: allelestate.alleleassessment.evaluation
            };
        }

    }

    prepareReferenceAssessmentsFromAlleleState(allele_id, analysis_id, allelestate) {
        let referenceassessments = [];
        if ('referenceassessment' in allelestate) {
            // Iterate over all referenceassessments for this allele
            for (let [reference_id, reference_state] of Object.entries(allelestate.referenceassessment)) {
                // If id is included, we're reusing an existing one.
                if ('id' in reference_state) {
                    referenceassessments.push({
                        allele_id: allele_id,
                        reference_id: parseInt(reference_id),
                        id: reference_state.id,
                        analysis_id: analysis_id
                    });
                }
                else {
                    // Fill in fields expected by backend
                    referenceassessments.push({
                        allele_id: allele_id,
                        reference_id: parseInt(reference_id),
                        analysis_id: analysis_id,
                        evaluation: reference_state.evaluation || {},
                        user_id: this.user.getCurrentUserId()
                    });
                }
            }
        }
        return referenceassessments;
    }

}


export default InterpretationService;
