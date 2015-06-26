/* jshint esnext: true */

(function() {

    angular.module('workbench')
        .factory('Interpretation', ['InterpretationResource', function(InterpretationResource) {
            return new Interpretation(InterpretationResource);
    }]);


    class Interpretation {

        constructor(interpretationResource) {
            this.interpretationResource = interpretationResource;
            this.currentInterpretation = null;
        }

        loadInterpretation(id) {
            return new Promise((resolve, reject) => {
                if (this.currentInterpretation) {
                    reject('Interpretation already loaded.');
                }
                else {
                    this.interpretationResource.getById(id).then(i => {
                        i.analysis.type = 'singlesample'; // TODO: remove me
                        this.currentInterpretation = i;
                        resolve(i);
                    });
                }
            });
        }

        getCurrent() {
            return this.currentInterpretation;
        }

        hasCurrent() {
            return Boolean(this.currentInterpretation);
        }

        abortCurrent() {
            this.currentInterpretation = null;
        }


    }

})();

