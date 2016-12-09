/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-hgmd',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/alleleInfoHgmd.ngtmpl.html'
})
@Inject()
export class AlleleInfoHgmd {

    constructor() {
        if (!this.hasContent()) {
            this.collapsed = true;
        }
    }

    hasContent() {
        return 'HGMD' in this.allele.annotation.external;
    }
}
