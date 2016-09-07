/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-frequency-indb',
    scope: {
        allele: '=',
        collapsed: '=?'
    },
    templateUrl: 'ngtmpl/alleleInfoFrequencyIndb.ngtmpl.html'
})
@Inject()
export class AlleleInfoFrequencyIndb {

    constructor() {
        if (!this.hasContent()) {
            this.collapsed = true;
        }
    }

    hasContent() {
        return 'inDB' in this.allele.annotation.frequencies;
    }

}
