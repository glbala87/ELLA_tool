/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-frequency-indb',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/alleleInfoFrequencyIndb.ngtmpl.html'
})
@Inject()
export class AlleleInfoFrequencyIndb {

    constructor() {}

}
