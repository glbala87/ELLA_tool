/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-frequency-esp6500',
    scope: {
        allele: '=',
        cbOptions: '='
    },
    templateUrl: 'ngtmpl/alleleInfoFrequencyEsp6500.ngtmpl.html'
})
@Inject()
export class AlleleInfoFrequencyEsp6500 {

    constructor() {

        this.checkForContent();

        this.cbOptions.title = "ESP6500";
        this.cbOptions.url = this.allele.getESP6500Url();
    }

    checkForContent() {
        if (!this.hasContent()) {
            this.cbOptions.disabled = true;
            this.cbOptions.collapsed = true;
        };
    }

    hasContent() {
        return 'esp6500' in this.allele.annotation.frequencies;
    }

}
