/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-frequency-gnomad-genomes',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/alleleInfoFrequencyGnomadGenomes.ngtmpl.html'
})
@Inject()
export class AlleleInfoFrequencyGnomadGenomes {

    constructor() {
    }

    hasContent() {
        return 'GNOMAD_GENOMES' in this.allele.annotation.frequencies;
    }
}
