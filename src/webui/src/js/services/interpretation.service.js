/* jshint esnext: true */

import {Service, Inject} from '../ng-decorators';
/**
 * Controller for dialog asking user whether to complete or finalize interpretation.
 */
class ConfirmCompleteInterpretationController {

    constructor(modalInstance, complete, finalize) {
        this.modal = modalInstance;
    }
}


@Service({
    serviceName: 'Interpretation'
})
@Inject('$rootScope',
        'Allele',
        'InterpretationResource',
        'ACMG',
        'User',
        '$uibModal',
        '$location')
class InterpretationService {

    constructor(rootScope,
        Allele,
        interpretationResource,
        ACMG,
        User,
        ModalService,
        LocationService) {


        this._setWatchers(rootScope);
        this.alleleService = Allele;
        this.user = User;
        this.interpretationResource = interpretationResource;
        this.acmg = ACMG;
        this.interpretation = null;
        this.modalService = ModalService;
        this.locationService = LocationService;
    }

    _setWatchers(rootScope) {
        // Watch interpretation's state/userState and call update whenever it changes
        let watchStateFn = () => {
            if (this.interpretation &&
                this.interpretation.state) {
                return this.interpretation.state;
            }
        };
        let watchUserStateFn = () => {
            if (this.interpretation &&
                this.interpretation.userState) {
                return this.interpretation.userState;
            }
        };
        rootScope.$watch(watchStateFn, (n, o) => {
            // If no old object, we're on the first iteration
            // -> don't set dirty
            if (this.interpretation && o) {
                this.interpretation.setDirty();
            }
        }, true); // true -> Deep watch

        rootScope.$watch(watchUserStateFn, (n, o) => {
            if (this.interpretation && o) {
                this.interpretation.setDirty();
            }
        }, true); // true -> Deep watch
    }

    loadInterpretation(id) {
        if (id === undefined) {
            throw Error("You must provide an id");
        }
        return new Promise((resolve, reject) => {
            if (this.interpretation) {
                reject('Interpretation already loaded.');
            } else {

                let puser = this.user.getCurrentUser();
                let pint = this.interpretationResource.get(id);

                // Prepare interpretation and assign user
                Promise.all([puser, pint]).spread((user, interpretation) => {
                    interpretation.analysis.type = 'singlesample'; // TODO: remove me when implemented in backend
                });

                // Resolve final promise
                Promise.all([puser, pint]).spread((user, interpretation) => {
                    return this._reloadAlleles(interpretation).then(alleles => {
                        this.interpretation = interpretation;
                        console.log("Interpretation loaded", this.interpretation);
                        resolve(this.interpretation);
                    });
                });

            }
        });
    }

    reloadAlleles() {
        if (!this.interpretation) {
            throw new Error("Interpretation not loaded yet.");
        }
        return this._reloadAlleles(this.interpretation);
    }

    _reloadAlleles(interpretation) {
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

    getCurrent() {
        return this.interpretation;
    }

    hasCurrent() {
        return Boolean(this.interpretation);
    }

    abortCurrent() {
        this.interpretation = null;
    }

    /**
     * Saves the current state to server.
     * If the status is 'Not started',
     * we start the interpretation before saving.
     * @return {Promise} Promise that resolves upon completion.
     */
    save() {
        if (this.interpretation.status === 'Not started') {
            if (this.interpretation.user_id === null) {
                this.interpretation.user_id = this.user.getCurrentUserId();
            }
            return this.interpretationResource.start(this.interpretation.id,
                                                     this.user.getCurrentUserId()).then(
                () => {
                    this.interpretation.status = 'Ongoing';
                    // Update on server in case user made any changes
                    // before starting analysis.
                    return this.save();
                },
                // Rejected:
                () => {
                    // If an error when starting, reload interpretation as someone
                    // else might have started the interpretation already.
                    let int_id = this.interpretation.id;
                    this.abortCurrent();
                    return this.loadInterpretation(int_id);
                }
            );
        }
        else {
            return this.interpretationResource.updateState(this.interpretation).then(
                () => this.interpretation.setClean()
            );
        }
    }

    /**
     * Popups a confirmation dialog, asking to complete or finalize the interpretation
     */
    confirmCompleteFinalize() {
        let modal = this.modalService.open({
            templateUrl: 'ngtmpl/interpretationConfirmation.modal.ngtmpl.html',
            controller: ['$uibModalInstance', ConfirmCompleteInterpretationController],
            controllerAs: 'vm'
        });
        modal.result.then(res => {
            if (res === 'complete') {
                this.complete();
            } else if (res === 'finalize') {
                this.finalize();
            } else {
                throw `Got unknown option ${res} when confirming interpretation action.`;
            }
            return true;
        });
    }

    complete() {
        // TODO: Error handling
        return this.save().then(() => {
            this.interpretationResource.complete(this.interpretation.id).then(() => {
                this.redirect();
            });
        });
    }

    finalize() {
        // TODO: Error handling
        return this.save().then(() => {
            this.interpretationResource.finalize(this.interpretation.id).then(() => {
                this.redirect();
            });
        });
    }

    redirect() {
        this.locationService.url('/analyses');
    }

    createOrUpdateReferenceAssessment(state_ra, allele, reference) {

        // Make copy and add/update mandatory fields before submission
        let copy_ra = Object.assign({}, state_ra);



        // Update the interpretation state on the server, in order to make sure everything is in sync.
        return this.alleleService.createOrUpdateReferenceAssessment(copy_ra).then(updated_ra => {

            // Update interpretation on server to reflect state changes made.
            this.save();

            // Update the ACMG code for allele in question.
            // Need to get all ReferenceAssessment for allele, not just the updated one
            let referenceassessment_ids = Object.values(
                this.interpretation.state.allele[allele.id].referenceassessment
            ).map(e => e.id).filter(e => e !== undefined);

            this.alleleService.updateACMG(
                [allele],
                referenceassessment_ids,
                this.interpretation.analysis.genepanel.name,
                this.interpretation.analysis.genepanel.version
            );
        });
    }

    createOrUpdateAlleleAssessment(state_aa, allele) {
        return this.alleleService.createOrUpdateAlleleAssessment(
            state_aa,
            allele,
            this.interpretation.analysis.genepanel.name,
            this.interpretation.analysis.genepanel.version,
            this.interpretation.id
        ).then(state_aa => {
            // Update interpretation on server to reflect state changes made.
            // (state_aa object is updated by the function, and is
            // part of interpretation's state)
            return this.save();
        });
    }

}


export default InterpretationService;
