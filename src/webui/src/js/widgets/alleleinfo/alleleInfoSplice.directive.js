/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-splice',
    scope: {
        allele: '=',
        cbOptions: '='
    },
    templateUrl: 'ngtmpl/alleleInfoSplice.ngtmpl.html'
})
@Inject()
export class AlleleInfoSplice {

    constructor() {

        this.cbOptions.title = "Splice";

        this.checkForContent();
    }

    checkForContent() {
        if (!this.hasContent()) {
            this.cbOptions.disabled = true;
            this.cbOptions.collapsed = true;
        };
    }

    hasContent() {
        return this.allele.annotation.filtered.some(t => 'Splice' in t);
    }
}
