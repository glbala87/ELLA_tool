/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-quality',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/alleleInfoQuality.ngtmpl.html'
})
@Inject()
export class AlleleInfoQuality {

    constructor() {}

    getVerificationText() {
        return this.allele.annotation.quality.needs_verification ? 'Yes' : 'No';
    }

    getGenotypeForSample() {
        // TODO: Fix me when introducing multiple samples...
        let sample_ids = Object.keys(this.allele.genotype);
        if (sample_ids.length) {
            return this.allele.genotype[sample_ids[0]];
        }
        return null;
    }
}
