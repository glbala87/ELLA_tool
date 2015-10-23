/* jshint esnext: true */

(function () {
    angular.module('workbench')
        .factory('AlleleFilter', ['Config', function (Config) {
            return new AlleleFilter(Config);
        }]);


    class AlleleFilter {

        constructor(Config) {
            this.config = Config.getConfig();

        }

        filterClass1(alleles) {

            let included = [];
            for (let a of alleles) {
                let exclude = false;
                for (let [key, criteria] of Object.entries(this.config.freq_criteria)) {
                    if (!exclude && key in a.annotation.annotations.frequencies) {
                        exclude = Object.values(a.annotation.annotations.frequencies[key]).some(elem => {
                            return elem > criteria;
                        });
                    }
                }
                if (!exclude) {
                    included.push(a);
                }
            }
            return included;

        }

        /**
         * Filters away any alleles with intron_variant as Consequence.
         * @return {Array} Filtered array of alleles.
         */
        filterIntronicAlleles(alleles) {
            return alleles.filter(a => {
                // Check that all Consequence fields in all filtered transcripts
                // only include 'intron_variant' and nothing else
                return !(a.annotation.filtered.every(e => {
                    return e.Consequence.length === 1 &&
                           e.Consequence[0]  === 'intron_variant';
                }));
            });
        }

        /**
         * Inverts an array of alleles, returning full - sub.
         * @return {Array} Alleles found in full, but not in sub.
         */
        invert(sub, full) {
            return full.filter(a => {
                return sub.findIndex(i => i === a) === -1;
            });
        }
    }

})();
