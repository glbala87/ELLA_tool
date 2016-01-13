/* jshint esnext: true */

import {Allele} from '../model/allele';
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
        'InterpretationResource',
        'ReferenceResource',
        'ACMG',
        'AlleleAssessmentResource',
        'User',
        '$modal',
        '$location')
class InterpretationService {

    constructor(rootScope,
        interpretationResource,
        referenceResource,
        ACMG,
        alleleAssessmentResource,
        User,
        ModalService,
        LocationService) {


        this._setWatchers(rootScope);

        this.user = User;
        this.interpretationResource = interpretationResource;
        this.referenceResource = referenceResource;
        this.acmg = ACMG;
        this.alleleAssessmentResource = alleleAssessmentResource;
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

                // Fetch alleles for this interpretation id
                let palleles = this.interpretationResource.getAlleles(id).then(alleles => {
                    let alleles_obj = [];
                    for (let allele of alleles) {
                        alleles_obj.push(new Allele(allele));
                    }
                    return alleles_obj;
                });

                // Add alleles and load references
                let prefs = Promise.all([pint, palleles]).spread((interpretation, alleles) =>{

                    // Add alleles to interpretation object
                    interpretation.setAlleles(alleles);

                    // Load references
                    let pmids = this._getPubmedIds(interpretation.alleles);
                    return this.referenceResource.getByPubMedIds(pmids);
                });

                // Load ReferenceAssessments
                let prefassm = Promise.all([prefs, palleles]).spread((refs, alleles) => {
                    let reference_ids = refs.map(r => r.id);
                    let allele_ids = alleles.map(a => a.id);
                    return this.referenceResource.getReferenceAssessments(allele_ids, reference_ids);
                });

                // Load AlleleAssessments
                let palleleassm = palleles.then(alleles => {
                    let allele_ids = alleles.map(a => a.id);
                    return this.alleleAssessmentResource.getByAlleleIds(allele_ids);
                });

                // Assign ReferenceAsessments/AlleleAssessments to interpretation
                let pint_prepared = Promise.all([pint, prefs, prefassm, palleleassm]).spread((interpretation, references, refassm, alleleassm) => {
                    interpretation.prepareAlleles(references, refassm, alleleassm);
                    interpretation.copyReferenceAssessmentsToState(refassm);
                });

                // Resolve final promise
                Promise.all([puser, pint, pint_prepared]).spread((user, interpretation) => {
                    this.interpretation = interpretation;
                    console.log("Interpretation loaded", this.interpretation);
                    resolve(this.interpretation);
                });

            }
        });
    }

    /**
     * Retrives combined PubMed IDs for all alles in the interpretation.
     * Requires that alleles are already loaded into the interpretation.
     * @return {Array} Array of ids.
     */
    _getPubmedIds(alleles) {
        let ids = [];
        for (let allele of alleles) {
            Array.prototype.push.apply(ids, allele.getPubmedIds());
        }
        return ids;
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
            controller: ['$modalInstance', ConfirmCompleteInterpretationController],
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

        return this.user.getCurrentUser().then(user => {
            Object.assign(copy_ra, {
                allele_id: allele.id,
                reference_id: reference.id,
                genepanelName: this.interpretation.analysis.genepanel.name,
                genepanelVersion: this.interpretation.analysis.genepanel.version,
                interpretation_id: this.interpretation.id,
                status: 0,  // Status is set to 0. Finalization happens in another step.
                user_id: user.id
            });

            // Update the interpretation's state with the response to include the updated fields into relevant referenceassessment
            // We set 'evaluation' again to ensure frontend is synced with server.
            // Then we update the interpretation state on the server, in order to make sure everything is in sync.
            return this.referenceResource.createOrUpdateReferenceAssessment(copy_ra).then(updated_ra => {
                state_ra.id = updated_ra.id;
                state_ra.evaluation = updated_ra.evaluation;
                state_ra.interpretation_id = updated_ra.interpretation_id;

                // Update interpretation on server to reflect state changes made.
                this.save();

                // Update the ACMG code for allele in question.
                // Need to get all ReferenceAssessment for allele, not just the updated one
                let referenceassessment_ids = Object.values(this.interpretation.state.referenceassessment[allele.id])
                                              .map(e => e.id)
                                              .filter(e => e !== undefined);
                this.acmg.updateACMGCodes(
                    [allele],
                    referenceassessment_ids,
                    this.interpretation.analysis.genepanel.name,
                    this.interpretation.analysis.genepanel.version
                );
            });
        });
    }

    createOrUpdateAlleleAssessment(state_aa, allele) {

        // Make copy and add mandatory fields before submission
        let copy_aa = Object.assign({}, state_aa);
        delete copy_aa.user;  // Remove extra data
        delete copy_aa.secondsSinceUpdate;
        // TODO: Add transcript
        return this.user.getCurrentUser().then(user => {
            Object.assign(copy_aa, {
                allele_id: allele.id,
                annotation_id: allele.annotation.annotation_id,
                genepanelName: this.interpretation.analysis.genepanel.name,
                genepanelVersion: this.interpretation.analysis.genepanel.version,
                interpretation_id: this.interpretation.id,
                status: 0, // Status is set to 0. Finalization happens in another step.
                user_id: user.id
            });

            // Update the interpretation's state with the response to include the updated fields into relevant alleleassessment
            // We set 'evaluation' and 'classification' again to ensure frontend is synced with server.
            // Then we update the interpretation state on the server, in order to make sure everything is in sync.
            return this.alleleAssessmentResource.createOrUpdateAlleleAssessment(copy_aa).then(aa => {
                state_aa.id = aa.id;
                state_aa.classification = aa.classification;
                state_aa.evaluation = aa.evaluation;
                state_aa.interpretation_id = aa.interpretation_id;

                // Update interpretation on server to reflect state changes made.
                return this.save();
            });

        });

    }

}


export default InterpretationService;
