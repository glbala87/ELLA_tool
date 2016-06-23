/* jshint esnext: true */

import {Service, Inject} from '../ng-decorators';

@Service({
    serviceName: 'AlleleFilter'
})
@Inject('Config')
class AlleleFilter {

    constructor(Config) {
        this.config = Config.getConfig();

    }

    /**
     * Filters away alleles that doesn't have any frequency data.
     * @return {Array} Alleles with frequency data.
     */
    filterFrequency(alleles) {
        let included = [];
        for (let allele of alleles) {
            if (Object.keys(allele.annotation.frequencies).filter(k => {
                    return Object.keys(this.config.frequencies.groups).includes(k);
                }).length) {
                included.push(allele);
            }
        }
        return included;
    }

    /**
     * Filters away alleles that doesn't have any references.
     * @return {Array} Alleles with references as given by it's annotation.
     */
    filterReferences(alleles) {
        return alleles.filter(a => a.getPubmedIds().length > 0);
    }

    /**
     * Filters away alleles that doesn't have any existing allele assessment.
     * @return {Array} Alleles with references as given by it's annotation.
     */
    filterAlleleAssessment(alleles) {
        return alleles.filter(a => a.allele_assessment);
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

export default AlleleFilter;
