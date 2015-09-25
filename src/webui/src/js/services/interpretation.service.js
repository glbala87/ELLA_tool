/* jshint esnext: true */

(function () {

    angular.module('workbench')
        .factory('Interpretation', ['$rootScope',
            'InterpretationResource',
            'ReferenceResource',
            'AlleleAssessmentResource',
            'User',
            '$modal',
            '$location',
            function ($rootScope,
                InterpretationResource,
                ReferenceResource,
                AlleleAssessmentResource,
                User,
                ModalService,
                LocationService) {

                return new Interpretation($rootScope,
                    InterpretationResource,
                    ReferenceResource,
                    AlleleAssessmentResource,
                    User,
                    ModalService,
                    LocationService);
            }
        ]);


    /**
     * Controller for dialog asking user whether to complete or finalize interpretation.
     */
    class ConfirmCompleteInterpretationController {

        constructor(modalInstance, complete, finalize) {
            this.modal = modalInstance;
        }
    }

    class Interpretation {

        constructor(rootScope,
            interpretationResource,
            referenceResource,
            alleleAssessmentResource,
            User,
            ModalService,
            LocationService) {


            this._setWatchers(rootScope);

            this.user = User;
            this.interpretationResource = interpretationResource;
            this.referenceResource = referenceResource;
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
            return new Promise((resolve, reject) => {
                if (this.interpretation) {
                    reject('Interpretation already loaded.');
                } else {

                    // TODO: Fix promise chaining mess
                    // Get user id (we need to assign it to the interpretation)
                    this.user.getCurrentUser().then(user => {

                        // Load main interpretation object
                        this.interpretationResource.get(id).then(i => {
                            i.analysis.type = 'singlesample'; // TODO: remove me when implemented in backend
                            i.user_id = user.id;
                            this.interpretation = i;

                            // Load alleles and add to object
                            this.interpretationResource.getAlleles(id).then(alleles => {
                                this.interpretation.setAlleles(alleles);

                                // Load references and add to object
                                let pmids = this._getPubmedIds();
                                this.referenceResource.getByPubMedIds(pmids).then(refs => {
                                    this.interpretation.setReferences(refs);
                                    console.log(refs);
                                    let reference_ids = refs.map(r => r.id);
                                    let allele_ids = alleles.map(a => a.id);

                                    // Load existing ReferenceAssessments for matching alleles/references.
                                    this.referenceResource.getReferenceAssessments(allele_ids, reference_ids).then(referenceassessments => {
                                        this.interpretation.setReferenceAssessments(referenceassessments);

                                        // Load existing AlleleAssessments for matching alleles
                                        this.alleleAssessmentResource.getByAlleleIds(allele_ids).then(alleleassessments => {
                                            this.interpretation.setAlleleAssessments(alleleassessments);
                                            resolve(this.interpretation);
                                        });
                                    });
                                });

                            });
                        });

                    });
                }
            });
        }

        /**
         * Retrives combined PubMed IDs for all alles in the interpretation.
         * Requires that alleles are already loaded into the interpretation.
         * @return {Array} Array of ids.
         */
        _getPubmedIds() {
            let ids = [];
            for (let allele of this.interpretation.alleles) {
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
         * If the status is 'Not started', we start the interpretation by
         * setting it to 'Ongoing'.
         * @return {Promise} Promise that resolves upon completion.
         */
        update() {
            if (this.interpretation.status === 'Not started') {
                this.interpretation.status = 'Ongoing';
            }
            return this.interpretationResource.updateState(this.interpretation).then(
                () => this.interpretation.setClean()
            );
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
                    this._complete();
                } else if (res === 'finalize') {
                    this._finalize();
                } else {
                    throw `Got unknown option ${res} when confirming interpretation action.`;
                }
                return true;
            });
        }

        _complete() {
            // TODO: Error handling
            return this.update().then(() => {
                this.interpretationResource.complete(this.interpretation.id).then(() => {
                    this.redirect();
                });
            });
        }

        _finalize() {
            // TODO: Error handling
            return this.update().then(() => {
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
                    return this.update();
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
                    annotation_id: allele.annotation.id,
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
                    return this.update();
                });

            });

        }

    }


})();
