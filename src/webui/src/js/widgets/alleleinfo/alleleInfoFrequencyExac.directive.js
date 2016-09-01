/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-frequency-exac',
    scope: {
        allele: '=',
        cbOptions: '='
    },
    templateUrl: 'ngtmpl/alleleInfoFrequencyExac.ngtmpl.html'
})
@Inject()
export class AlleleInfoFrequencyExac {

    constructor() {

        this.checkForContent();
        this.cbOptions.title = "ExAC";
        this.cbOptions.url = this.allele.getExACUrl();
    }

    checkForContent() {
        if (!this.hasContent()) {
            this.cbOptions.disabled = true;
            this.cbOptions.collapsed = true;
        };
    }

    hasContent() {
        return 'ExAC' in this.allele.annotation.frequencies;
    }
}
