/* jshint esnext: true */

(function() {

    angular.module('workbench')
        .factory('Interpretation', ['$rootScope',
                                    'InterpretationResource',
                                    'ReferenceResource',
                                    'User',
                                    function($rootScope,
                                             InterpretationResource,
                                             ReferenceResource,
                                             User) {

            return new Interpretation($rootScope,
                                      InterpretationResource,
                                      ReferenceResource,
                                      User);
    }]);


    class Interpretation {

        constructor(rootScope, interpretationResource, referenceResource, User) {


            this._setWatchers(rootScope);

            this.user = User;
            this.interpretationResource = interpretationResource;
            this.referenceResource = referenceResource;
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
                if (this.interpretation) {
                    this.interpretation.stateChanged();
                }
            }, true);  // true -> Deep watch

            rootScope.$watch(watchUserStateFn, (n, o) => {
                if (this.interpretation) {
                    this.interpretation.userStateChanged();
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
                        // Load main object
                        this.interpretationResource.get(id).then(i => {
                            i.analysis.type = 'singlesample'; // TODO: remove me
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
                                        this.interpretationResource.getAlleleAssessments(this.interpretation.id).then(alleleassessments => {
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
         * @return {Promise} Promise that resolves upon update.
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

    }

})();

