/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-frequency-exac',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/alleleInfoFrequencyExac.ngtmpl.html'
})
@Inject()
export class AlleleInfoFrequencyExac {

    constructor() {
    }

    hasContent() {
        return 'ExAC' in this.allele.annotation.frequencies;
    }
}
