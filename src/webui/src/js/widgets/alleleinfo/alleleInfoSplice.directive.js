/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-splice',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/alleleInfoSplice.ngtmpl.html'
})
@Inject()
export class AlleleInfoSplice {

    constructor() {}

    hasContent() {
        return this.allele.annotation.filtered.some(t => 'Splice' in t);
    }
}
