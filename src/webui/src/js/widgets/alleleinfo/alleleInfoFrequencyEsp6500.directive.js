/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-frequency-esp6500',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/alleleInfoFrequencyEsp6500.ngtmpl.html'
})
@Inject()
export class AlleleInfoFrequencyEsp6500 {

    constructor() {}

}
