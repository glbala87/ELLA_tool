/* jshint esnext: true */

(function() {

    angular.module('workbench')
        .factory('Interpretation', ['$rootScope', 'InterpretationResource', 'ReferenceResource', function($rootScope, InterpretationResource, ReferenceResource) {
            return new Interpretation($rootScope, InterpretationResource, ReferenceResource);
    }]);


    class Interpretation {

        constructor(rootScope, interpretationResource, referenceResource) {

            // Watch interpretation's state and call update whenever it changes
            let watchFn = () => {
                if (this.interpretation &&
                    this.interpretation.state) {
                    return this.interpretation.state;
                }
            };
            rootScope.$watch(watchFn, () => {
                if (this.interpretation) {
                    this.interpretation.stateChanged();
                }
            }, true);  // true -> Deep watch

            this.interpretationResource = interpretationResource;
            this.referenceResource = referenceResource;
            this.interpretation = null;
        }

        loadInterpretation(id) {
            return new Promise((resolve, reject) => {
                if (this.interpretation) {
                    reject('Interpretation already loaded.');
                }
                else {
                    // Load main object
                    this.interpretationResource.get(id).then(i => {
                        i.analysis.type = 'singlesample'; // TODO: remove me
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
            return this.interpretationResource.updateState(this.interpretation);
        }

        createOrUpdateReferenceAssessment(ra) {
            return this.referenceResource.createOrUpdateReferenceAssessment(ra).then(updated => {
                this.interpretation.setReferenceAssessments([updated]);
            });
        }

    }

})();

