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
        'ACMG',
        'User',
        '$uibModal',
        '$location')
class InterpretationService {

    constructor(rootScope,
        Allele,
        Analysis,
        interpretationResource,
        ACMG,
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
/*
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
    }*/

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
            if (res === 'markreview') {
                this.analysisService.markreview(interpretation.analysis.id);
            } else if (res === 'finalize') {
                this.analysisService.finalize(interpretation.analysis.id);
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



}


export default InterpretationService;
