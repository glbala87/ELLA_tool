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

    constructor() {
        if (!this.hasContent()) {
            this.collapsed = true;
        }
    }

    hasContent() {
        return this.allele.annotation.filtered.some(t => 'splice' in t);
    }
}
