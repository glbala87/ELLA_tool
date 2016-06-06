/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-consequence',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/alleleInfoConsequence.ngtmpl.html'
})
@Inject()
export class AlleleInfoVariantConsequence {

    constructor() {}

}
