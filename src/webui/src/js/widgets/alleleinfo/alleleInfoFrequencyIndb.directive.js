/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-frequency-indb',
    scope: {
        allele: '=',
        cbOptions: '='
    },
    templateUrl: 'ngtmpl/alleleInfoFrequencyIndb.ngtmpl.html'
})
@Inject()
export class AlleleInfoFrequencyIndb {

    constructor() {
        this.cbOptions.title = 'inDB';

        this.checkForContent();
    }

    checkForContent() {
        if (!this.hasContent()) {
            this.cbOptions.disabled = true;
            this.cbOptions.collapsed = true;
        };
    }

    hasContent() {
        return 'inDB' in this.allele.annotation.frequencies;
    }

}
