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

    filterClass1(alleles) {

        let included = [];
        for (let a of alleles) {
            let exclude = false;
            for (let [key, subkeys] of Object.entries(this.config.frequencies.criterias)) {
                for (let [subkey, criteria] of Object.entries(subkeys)) {
                    if (!exclude &&
                        key in a.annotation.frequencies &&
                        subkey in a.annotation.frequencies[key]) {
                        exclude = a.annotation.frequencies[key][subkey] > criteria;
                    }
                }
            }
            if (!exclude) {
                included.push(a);
            }
        }
        return included;

    }

    /**
     * Filters away any alleles with intron_variant as Consequence
     * and that are outside range given in config.
     * @return {Array} Filtered array of alleles.
     */
    filterIntronicAlleles(alleles) {
        // Matches NM_007294.3:c.4535-213G>T  (gives ['-', '213'])
        // but not NM_007294.3:c.4535G>T
        let reg_exp = /.*c\.[0-9]+?([\-\+])([0-9]+)/;
        return alleles.filter(a => {
            if (!a.annotation.filtered.length) {
                return true;  // Always include if no filtered transcripts
            }
            // Only exclude if variant is outside range given in config
            // as given by the cDNA
            // If the format is different, don't filter variant.
            return !(a.annotation.filtered.every(e => {
                let cdna_pos = reg_exp.exec(e.HGVSc);
                if (!cdna_pos || !cdna_pos.length) {  // No match, include it
                    return false;
                }
                else {
                    let [first, sign, pos] = cdna_pos;
                    pos = parseInt(pos, 10);
                    let criteria = this.config.variant_criteria.intronic_region;
                    if (sign in criteria) {
                        return pos > criteria[sign];
                    }
                    else {
                        return false;
                    }
                }

            }));
        });
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
