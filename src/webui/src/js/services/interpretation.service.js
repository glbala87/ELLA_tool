/* jshint esnext: true */

(function() {

    angular.module('workbench')
        .factory('Interpretation', ['$rootScope',
                                    'InterpretationResource',
                                    'ReferenceResource',
                                    'AlleleAssessmentResource',
                                    'User',
                                    function($rootScope,
                                             InterpretationResource,
                                             ReferenceResource,
                                             AlleleAssessmentResource,
                                             User) {

            return new Interpretation($rootScope,
                                      InterpretationResource,
                                      ReferenceResource,
                                      AlleleAssessmentResource,
                                      User);
    }]);


    class Interpretation {

        constructor(rootScope,
                    interpretationResource,
                    referenceResource,
                    alleleAssessmentResource,
                    User) {


            this._setWatchers(rootScope);

            this.user = User;
            this.interpretationResource = interpretationResource;
            this.referenceResource = referenceResource;
            this.alleleAssessmentResource = alleleAssessmentResource;
            this.interpretation = null;
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
            }, true);  // true -> Deep watch

            rootScope.$watch(watchUserStateFn, (n, o) => {
                if (this.interpretation && o) {
                    this.interpretation.setDirty();
                }
            }, true);  // true -> Deep watch
        }

        loadInterpretation(id) {
            return new Promise((resolve, reject) => {
                if (this.interpretation) {
                    reject('Interpretation already loaded.');
                }
                else {

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

                                    // Load reference assessments and add to object
                                    this.interpretationResource.getReferenceAssessments(this.interpretation.id).then(referenceassessments => {
                                        this.interpretation.setReferenceAssessments(referenceassessments);

                                        // Load allele assessments and add to object
                                        let allele_ids = alleles.map(al => al.id);
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
                () => this.interpretation.dirty = false
            );
        }

        createOrUpdateReferenceAssessment(ra) {
            return this.referenceResource.createOrUpdateReferenceAssessment(ra).then(updated => {
                this.interpretation.setReferenceAssessments([updated]);
            });
        }

        createOrUpdateAlleleAssessment(aa, allele) {

            // TODO: This might not be the best approach as it might be possible to go out of sync
            // with alleleassessment on server. Consider updating state from fetching alleleassessments
            // when loading a new report, in addition to relying on saving the state before saving the
            // alleleassessment to keep them in sync.

            this.update().then(i => {
                // Make copy and add mandatory fields before submission
                let copy_aa = Object.assign({}, aa);
                Object.assign(copy_aa, {
                    allele_id: allele.id,
                    annotation_id: allele.annotation.id,
                    genepanelName: this.interpretation.analysis.genepanel.name,
                    genepanelVersion: this.interpretation.analysis.genepanel.version,
                    interpretation_id: this.interpretation.id,
                    status: 0  // Status is set to 0. Finalization happens in another step.
                });

                // Update the interpretation's state with the response to include the updated fields into relevant alleleassessment
                // We set 'evaluation' and 'classification' again to ensure frontend is synced with server.
                return this.alleleAssessmentResource.createOrUpdateAlleleAssessment(copy_aa).then(aa => {
                    let state_aa = this.interpretation.state.alleleassessment[aa.allele_id];
                    state_aa.id = aa.id;
                    state_aa.classification = aa.classification;
                    state_aa.evaluation = aa.evaluation;
                });
            });

        }

    }

})();

