/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-frequency-gnomad-exomes',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/alleleInfoFrequencyGnomadExomes.ngtmpl.html'
})
@Inject()
export class AlleleInfoFrequencyGnomadExomes {

    constructor() {
    }

    hasContent() {
        return 'GNOMAD_EXOMES' in this.allele.annotation.frequencies;
    }
}
